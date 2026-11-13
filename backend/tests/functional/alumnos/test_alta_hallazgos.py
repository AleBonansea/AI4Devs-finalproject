"""Capability `alumnos`: `POST /api/v1/alumnos`, Scenarios agregados por el
pase adversarial (change familias-y-alumnos, tarea 9.2).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/alumnos/spec.md`:
- «Quién puede dar de alta un alumno»: «Profesor con un grupo ajeno
  inactivo» y «Profesor con un grupo que no existe».
- «Personas en el alta»: «Persona nueva con un DNI ya cargado escrito con
  guiones» y «Dos altas a la vez con el mismo DNI nuevo».

La preparacion sigue a `alumnos/test_alta.py`: usuarios y temporada con el
ORM, grupos, familias y personas con SQL crudo, tokens del login real, y los
efectos leidos con SQL desde la sesion del test.

**La carrera.** «Dos altas a la vez» se provoca de verdad sobre la conexion
compartida de la fixture `conexion` (la misma que usa la sesion de la API):
un oyente `before_cursor_execute` de SQLAlchemy, la primera vez que ve un
`INSERT INTO persona` cuyos parametros llevan el DNI `40222333`, inserta antes
otra persona con ese DNI por un cursor crudo de la misma conexion (que no
dispara eventos, asi no hay recursion). Cualquier comprobacion previa del
servicio corrio antes y no vio el DNI; el INSERT del alta choca entonces con
la restriccion unica de la base. El test afirma que el oyente se disparo, asi
que no puede aprobarse sin haber provocado la carrera.
"""

import re
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, event, text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_ALUMNOS = "/api/v1/alumnos"
CONTRASENA = "Verano2026"

MENSAJE_GRUPO_AJENO = "Solo podés inscribir alumnos en tus grupos."
MENSAJE_DNI_CARGADO = "Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla."

TABLAS = ("familia", "persona", "familia_persona", "alumno", "inscripcion")

DNI_DE_LA_CARRERA = "40222333"
_INSERT_EN_PERSONA = re.compile(r'^\s*INSERT\s+INTO\s+"?persona"?[\s(]', re.IGNORECASE)


# --- preparacion -----------------------------------------------------------


def _crear_usuario(sesion: Session, username: str, rol: RolUsuario) -> int:
    usuario = Usuario(
        username=username,
        password_hash=hashear(CONTRASENA),
        debe_cambiar_password=False,
        intentos_fallidos=0,
        nombre="Juan",
        apellido="Perez",
        rol=rol,
        activo=True,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario.id


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _insertar_grupo(
    sesion: Session, temporada_id: int, nombre: str, turno: str, *, activo: bool = True
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, :n, :tu, :d, :h, :a) RETURNING id"
            ),
            {
                "t": temporada_id,
                "n": nombre,
                "tu": turno,
                "d": date(2020, 1, 1),
                "h": date(2021, 12, 31),
                "a": activo,
            },
        ).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def _familia_perez_ana(sesion: Session) -> None:
    """La familia `Pérez – Ana`, categoría `empleado`, con María Pérez
    (DNI 30111222) como tutora."""
    familia = int(
        sesion.execute(
            text("INSERT INTO familia (categoria) VALUES ('empleado') RETURNING id")
        ).scalar_one()
    )
    sesion.execute(
        text(
            "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
            "VALUES (:f, 'Ana', 'Pérez', :fn)"
        ),
        {"f": familia, "fn": date(2018, 7, 5)},
    )
    maria = int(
        sesion.execute(
            text(
                "INSERT INTO persona (nombre, apellido, telefono, dni) "
                "VALUES ('María', 'Pérez', '3511234567', '30111222') RETURNING id"
            )
        ).scalar_one()
    )
    sesion.execute(
        text(
            "INSERT INTO familia_persona "
            "(familia_id, persona_id, es_tutor, autorizado_retiro, contacto_emergencia) "
            "VALUES (:f, :p, true, true, false)"
        ),
        {"f": familia, "p": maria},
    )


def _id_inexistente(sesion: Session, tabla: str) -> int:
    return int(
        sesion.execute(text(f"SELECT coalesce(max(id), 0) + 1000 FROM {tabla}")).scalar_one()
    )


def _conteos(sesion: Session) -> dict[str, int]:
    return {
        tabla: int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())
        for tabla in TABLAS
    }


def _persona_nueva(dni: str) -> dict[str, Any]:
    return {
        "nombre": "Laura",
        "apellido": "Gómez",
        "telefono": "3512223333",
        "dni": dni,
        "es_tutor": True,
    }


def _cuerpo(grupo_id: int, **cambios: Any) -> dict[str, Any]:
    """Un alta valida de Juan Pérez con familia nueva `empleado` y María Pérez
    nueva (DNI 30111222) como tutora. `cambios` pisa claves."""
    cuerpo: dict[str, Any] = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "fecha_nacimiento": "2020-03-10",
        "grupo_id": grupo_id,
        "categoria": "empleado",
        "personas": [
            {
                "nombre": "María",
                "apellido": "Pérez",
                "telefono": "3511234567",
                "dni": "30111222",
                "es_tutor": True,
            }
        ],
    }
    cuerpo.update(cambios)
    return cuerpo


def _afirmar_error(respuesta: Any, campo: tuple[str | int, ...], msg: str) -> None:
    """422 y los errores cuyo `loc`, sin `"body"`, es `campo`: uno, con `msg`."""
    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    encontrados = []
    for error in detalle:
        loc = list(error["loc"])
        if loc and loc[0] == "body":
            loc = loc[1:]
        if loc == list(campo):
            encontrados.append(error)
    assert [e["msg"] for e in encontrados] == [msg], respuesta.text


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    return _insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


@pytest.fixture
def profesor_de_delfines(
    cliente: TestClient, sesion: Session, delfines_manana: int
) -> dict[str, str]:
    """Un Profesor asignado solo a «Delfines» mañana."""
    profesor = _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
    _asignar(sesion, delfines_manana, profesor)
    return _ingresar(cliente, "jperez")


# --- Requirement: Quién puede dar de alta un alumno ------------------------


class TestQuienPuedeDarDeAltaHallazgos:
    def test_el_profesor_con_un_grupo_ajeno_inactivo_recibe_403_y_no_se_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Profesor con un grupo ajeno inactivo
        pulpos = _insertar_grupo(sesion, vigente, "Pulpos", "manana", activo=False)
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(pulpos))

        # 403 y no el 422 «El grupo no está activo.»: el Profesor no se entera
        # de nada de un grupo ajeno.
        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert _conteos(sesion) == antes

    def test_el_profesor_con_un_grupo_que_no_existe_recibe_403_y_no_se_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Profesor con un grupo que no existe
        inexistente = _id_inexistente(sesion, "grupo")
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(inexistente)
        )

        # 403 y no el 422 «El grupo no existe.».
        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert _conteos(sesion) == antes


# --- Requirement: Personas en el alta --------------------------------------


class TestPersonasEnElAltaHallazgos:
    def test_una_persona_nueva_con_un_dni_ya_cargado_con_guiones_responde_422_en_su_dni(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Persona nueva con un DNI ya cargado escrito con guiones
        _familia_perez_ana(sesion)
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(
                delfines_manana,
                nombre="Lucía",
                apellido="Gómez",
                fecha_nacimiento="2020-02-02",
                categoria="socio",
                personas=[
                    {
                        "nombre": "María",
                        "apellido": "Pérez",
                        "telefono": "3511234567",
                        "dni": "30-111-222",
                        "es_tutor": True,
                    }
                ],
            ),
        )

        _afirmar_error(respuesta, ("personas", 0, "dni"), MENSAJE_DNI_CARGADO)
        assert _conteos(sesion) == antes

    def test_dos_altas_a_la_vez_con_el_mismo_dni_nuevo_responde_422_en_el_dni_y_no_500(
        self,
        cliente: TestClient,
        sesion: Session,
        conexion: Connection,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Dos altas a la vez con el mismo DNI nuevo
        # Nadie tiene todavia el DNI: la comprobacion previa no lo va a ver.
        con_el_dni = sesion.execute(
            text("SELECT count(*) FROM persona WHERE dni = :d"), {"d": DNI_DE_LA_CARRERA}
        ).scalar_one()
        assert con_el_dni == 0
        antes = _conteos(sesion)

        estado = {"disparado": False}

        def otra_alta_se_adelanta(
            conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
        ) -> None:
            if estado["disparado"]:
                return
            if not _INSERT_EN_PERSONA.match(statement):
                return
            if DNI_DE_LA_CARRERA not in repr(parameters):
                return
            estado["disparado"] = True
            # Cursor crudo de la misma conexion: no dispara eventos de
            # SQLAlchemy, y la fila queda en la misma transaccion que el alta.
            crudo = conn.connection.cursor()
            try:
                crudo.execute(
                    "INSERT INTO persona (nombre, apellido, telefono, dni) "
                    "VALUES ('Otra', 'Alta', '3519999999', '" + DNI_DE_LA_CARRERA + "')"
                )
            finally:
                crudo.close()

        event.listen(conexion, "before_cursor_execute", otra_alta_se_adelanta)
        try:
            respuesta = cliente.post(
                URL_ALUMNOS,
                headers=coordinador,
                json=_cuerpo(delfines_manana, personas=[_persona_nueva(DNI_DE_LA_CARRERA)]),
            )
        finally:
            event.remove(conexion, "before_cursor_execute", otra_alta_se_adelanta)

        # La carrera ocurrio de verdad: si no, el test no prueba nada.
        assert estado["disparado"], "el alta no llego a insertar la persona con el DNI"
        # THEN 422 en personas.0.dni con el mensaje, no 500.
        _afirmar_error(respuesta, ("personas", 0, "dni"), MENSAJE_DNI_CARGADO)
        # AND no se crea nada de esa alta. La persona de la «otra alta» puede
        # haberse ido con la reversion del alta, por eso `persona` no se compara.
        despues = _conteos(sesion)
        for tabla in ("familia", "familia_persona", "alumno", "inscripcion"):
            assert despues[tabla] == antes[tabla], (tabla, antes, despues)
        laura = sesion.execute(
            text("SELECT count(*) FROM persona WHERE nombre = 'Laura' AND apellido = 'Gómez'")
        ).scalar_one()
        assert laura == 0
