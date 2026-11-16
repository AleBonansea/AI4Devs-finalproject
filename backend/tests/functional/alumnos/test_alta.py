"""Capability `alumnos`: `POST /api/v1/alumnos` (change familias-y-alumnos, tarea 4.1).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/alumnos/spec.md`:
- «Alta de un alumno con familia nueva» (4 Scenarios).
- «Alta de un alumno en una familia existente» (4 Scenarios).
- «Personas en el alta» (7 Scenarios).
- «Datos del alumno en el alta» (4 Scenarios; «Faltan varios datos minimos»
  es de otra tarea).
- «El grupo del alta» (4 Scenarios).
- «Quién puede dar de alta un alumno» (5 Scenarios).

Se prueba por la API. El estado se prepara con la sesion del test: usuarios y
temporadas con el ORM, y grupos, familias, alumnos y personas con SQL crudo,
igual que `familias/test_busquedas.py`. Los tokens salen del login real.

Los efectos se leen con SQL desde la sesion del test. La API usa su propia
sesion sobre la misma conexion (ver `conftest.py`): si el servicio no
commitea, lo que escribio se revierte y estos conteos no lo ven, asi que un
«quedo guardado» puede fallar de verdad.

Un error «en `personas.0.dni`» es un elemento de `detail` cuyo `loc`, sin el
`"body"` inicial, es `["personas", 0, "dni"]`.
"""

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_ALUMNOS = "/api/v1/alumnos"
CONTRASENA = "Verano2026"

MENSAJE_GRUPO_AJENO = "Solo podés inscribir alumnos en tus grupos."

TABLAS = ("familia", "persona", "familia_persona", "alumno", "inscripcion")

# Marca para quitar una clave del cuerpo base.
OMITIR = object()


def _maria_nueva(**cambios: Any) -> dict[str, Any]:
    persona: dict[str, Any] = {
        "nombre": "María",
        "apellido": "Pérez",
        "telefono": "3511234567",
        "dni": "30111222",
        "es_tutor": True,
    }
    persona.update(cambios)
    return {k: v for k, v in persona.items() if v is not OMITIR}


def _raul_nuevo() -> dict[str, Any]:
    """Raúl Pérez, teléfono 3517654321, sin DNI, no tutor."""
    return {"nombre": "Raúl", "apellido": "Pérez", "telefono": "3517654321", "es_tutor": False}


# --- preparacion -----------------------------------------------------------


def _crear_usuario(
    sesion: Session, username: str, rol: RolUsuario, *, debe_cambiar_password: bool = False
) -> int:
    usuario = Usuario(
        username=username,
        password_hash=hashear(CONTRASENA),
        debe_cambiar_password=debe_cambiar_password,
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


def _crear_temporada(
    sesion: Session, nombre: str, estado: EstadoTemporada, inicio: date, cierre: date
) -> int:
    temporada = Temporada(nombre=nombre, fecha_inicio=inicio, fecha_cierre=cierre, estado=estado)
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def _insertar_grupo(
    sesion: Session,
    temporada_id: int,
    nombre: str,
    turno: str,
    desde: date,
    hasta: date,
    *,
    activo: bool = True,
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, :n, :tu, :d, :h, :a) RETURNING id"
            ),
            {"t": temporada_id, "n": nombre, "tu": turno, "d": desde, "h": hasta, "a": activo},
        ).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def _crear_familia(sesion: Session, categoria: str) -> int:
    return int(
        sesion.execute(
            text("INSERT INTO familia (categoria) VALUES (:c) RETURNING id"), {"c": categoria}
        ).scalar_one()
    )


def _crear_alumno(
    sesion: Session, familia_id: int, nombre: str, apellido: str, nacimiento: date
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
                "VALUES (:f, :n, :a, :fn) RETURNING id"
            ),
            {"f": familia_id, "n": nombre, "a": apellido, "fn": nacimiento},
        ).scalar_one()
    )


def _crear_persona(
    sesion: Session, nombre: str, apellido: str, dni: str | None, telefono: str
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO persona (nombre, apellido, telefono, dni) "
                "VALUES (:n, :a, :t, :d) RETURNING id"
            ),
            {"n": nombre, "a": apellido, "t": telefono, "d": dni},
        ).scalar_one()
    )


def _vincular_tutor(sesion: Session, familia_id: int, persona_id: int) -> None:
    sesion.execute(
        text(
            "INSERT INTO familia_persona "
            "(familia_id, persona_id, es_tutor, autorizado_retiro, contacto_emergencia) "
            "VALUES (:f, :p, true, true, false)"
        ),
        {"f": familia_id, "p": persona_id},
    )


def _familia_perez_juan(sesion: Session) -> tuple[int, int]:
    """La familia `Pérez – Juan`, categoría `empleado`: Juan nacido el
    2020-03-10 y María Pérez (DNI 30111222) como tutora. Devuelve
    (familia, María)."""
    familia = _crear_familia(sesion, "empleado")
    _crear_alumno(sesion, familia, "Juan", "Pérez", date(2020, 3, 10))
    maria = _crear_persona(sesion, "María", "Pérez", "30111222", "3511234567")
    _vincular_tutor(sesion, familia, maria)
    return familia, maria


def _familia_perez_ana(sesion: Session) -> tuple[int, int]:
    """La familia `Pérez – Ana`, categoría `empleado`: Juan (2020-03-10) y Ana
    (2018-07-05), con María Pérez (DNI 30111222) como tutora. Devuelve
    (familia, María)."""
    familia, maria = _familia_perez_juan(sesion)
    _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))
    return familia, maria


def _id_inexistente(sesion: Session, tabla: str) -> int:
    return int(
        sesion.execute(text(f"SELECT coalesce(max(id), 0) + 1000 FROM {tabla}")).scalar_one()
    )


def _conteos(sesion: Session) -> dict[str, int]:
    return {
        tabla: int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())
        for tabla in TABLAS
    }


def _vinculos(sesion: Session, familia_id: int) -> list[tuple[int, bool, bool]]:
    """(persona_id, es_tutor, autorizado_retiro) de cada vinculo de la familia."""
    filas = sesion.execute(
        text(
            "SELECT persona_id, es_tutor, autorizado_retiro FROM familia_persona "
            "WHERE familia_id = :f ORDER BY persona_id"
        ),
        {"f": familia_id},
    )
    return [(f[0], f[1], f[2]) for f in filas]


def _persona_por_nombre(sesion: Session, nombre: str, apellido: str) -> list[tuple[int, Any]]:
    filas = sesion.execute(
        text("SELECT id, dni FROM persona WHERE nombre = :n AND apellido = :a ORDER BY id"),
        {"n": nombre, "a": apellido},
    )
    return [(f[0], f[1]) for f in filas]


def _cuerpo(grupo_id: int, **cambios: Any) -> dict[str, Any]:
    """Un alta válida de Juan Pérez con familia nueva `empleado` y María Pérez
    nueva como tutora. `cambios` pisa claves; `OMITIR` las quita."""
    cuerpo: dict[str, Any] = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "fecha_nacimiento": "2020-03-10",
        "grupo_id": grupo_id,
        "categoria": "empleado",
        "personas": [_maria_nueva()],
    }
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not OMITIR}


def _errores_en(respuesta: Any, *campo: str | int) -> list[dict[str, Any]]:
    """Los errores de `detail` cuyo `loc`, sin el `"body"` inicial, es `campo`."""
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    encontrados = []
    for error in detalle:
        loc = list(error["loc"])
        if loc and loc[0] == "body":
            loc = loc[1:]
        if loc == list(campo):
            encontrados.append(error)
    return encontrados


def _afirmar_error(respuesta: Any, campo: tuple[str | int, ...], msg: str | None = None) -> None:
    assert respuesta.status_code == 422, respuesta.text
    errores = _errores_en(respuesta, *campo)
    assert errores, f"no hay error en {campo}: {respuesta.text}"
    if msg is not None:
        assert [e["msg"] for e in errores] == [msg], respuesta.text


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    return _crear_temporada(
        sesion, "2026-27", EstadoTemporada.VIGENTE, date(2026, 12, 14), date(2027, 2, 28)
    )


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    """«Delfines» mañana de la vigente, para nacidos del 2020-01-01 al 2021-12-31."""
    return _insertar_grupo(
        sesion, vigente, "Delfines", "manana", date(2020, 1, 1), date(2021, 12, 31)
    )


@pytest.fixture
def tiburones_manana(sesion: Session, vigente: int) -> int:
    """«Tiburones» mañana de la vigente, para nacidos del 2017-01-01 al 2019-12-31."""
    return _insertar_grupo(
        sesion, vigente, "Tiburones", "manana", date(2017, 1, 1), date(2019, 12, 31)
    )


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


# --- Requirement: Alta de un alumno con familia nueva ----------------------


class TestAltaConFamiliaNueva:
    def test_el_primer_hijo_crea_la_familia_el_alumno_la_inscripcion_y_la_tutora(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Primer hijo con su tutora
        antes = _conteos(sesion)

        # El cuerpo no trae ningun documento.
        respuesta = cliente.post(URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["nombre"] == "Juan"
        assert cuerpo["apellido"] == "Pérez"
        assert cuerpo["fecha_nacimiento"] == "2020-03-10"
        familia = cuerpo["familia"]
        assert familia["etiqueta"] == "Pérez – Juan"
        assert familia["categoria"] == "empleado"
        assert cuerpo["inscripcion"] == {
            "grupo_id": delfines_manana,
            "grupo_nombre": "Delfines",
            "turno": "manana",
            "temporada_id": vigente,
        }

        # Quedo guardado: una familia, un alumno, una persona, un vinculo y
        # una inscripcion mas.
        despues = _conteos(sesion)
        assert {t: despues[t] - antes[t] for t in TABLAS} == dict.fromkeys(TABLAS, 1)
        categoria = sesion.execute(
            text("SELECT categoria FROM familia WHERE id = :f"), {"f": familia["id"]}
        ).scalar_one()
        assert categoria == "empleado"
        alumno = sesion.execute(
            text("SELECT familia_id, nombre, apellido, fecha_nacimiento FROM alumno WHERE id = :a"),
            {"a": cuerpo["id"]},
        ).one()
        assert tuple(alumno) == (familia["id"], "Juan", "Pérez", date(2020, 3, 10))
        inscripcion = sesion.execute(
            text("SELECT grupo_id, temporada_id, turno FROM inscripcion WHERE alumno_id = :a"),
            {"a": cuerpo["id"]},
        ).one()
        assert tuple(inscripcion) == (delfines_manana, vigente, "manana")

        # AND María Pérez vinculada con es_tutor y autorizado_retiro en true.
        marias = _persona_por_nombre(sesion, "María", "Pérez")
        assert len(marias) == 1
        maria, dni = marias[0]
        assert dni == "30111222"
        telefono = sesion.execute(
            text("SELECT telefono FROM persona WHERE id = :p"), {"p": maria}
        ).scalar_one()
        assert telefono == "3511234567"
        assert _vinculos(sesion, familia["id"]) == [(maria, True, True)]

    def test_la_otra_persona_queda_vinculada_sin_ser_tutor_y_autorizada_a_retirar(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Tutora y otra persona autorizada
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[_maria_nueva(), _raul_nuevo()]),
        )

        assert respuesta.status_code == 201, respuesta.text
        familia = respuesta.json()["familia"]["id"]
        ((maria, _),) = _persona_por_nombre(sesion, "María", "Pérez")
        raules = _persona_por_nombre(sesion, "Raúl", "Pérez")
        assert len(raules) == 1
        raul, dni_raul = raules[0]
        assert dni_raul is None
        assert sorted(_vinculos(sesion, familia)) == sorted(
            [(maria, True, True), (raul, False, True)]
        )

    def test_una_familia_nueva_sin_tutor_responde_422_en_personas_y_no_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Familia nueva sin ningún tutor
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[_raul_nuevo()]),
        )

        _afirmar_error(respuesta, ("personas",), "La familia nueva necesita al menos un tutor.")
        assert _conteos(sesion) == antes

    def test_una_familia_nueva_sin_categoria_responde_422_en_categoria_y_no_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Familia nueva sin categoría
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, categoria=OMITIR)
        )

        _afirmar_error(respuesta, ("categoria",))
        assert _conteos(sesion) == antes


# --- Requirement: Alta de un alumno en una familia existente ---------------


class TestAltaEnFamiliaExistente:
    def test_el_segundo_hijo_entra_en_la_misma_familia_que_conserva_categoria_y_tutora(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        tiburones_manana: int,
    ) -> None:
        # Scenario: Segundo hijo, en otro grupo
        familia, maria = _familia_perez_juan(sesion)
        _crear_usuario(sesion, "admin1", RolUsuario.ADMIN)
        encabezados = _ingresar(cliente, "admin1")
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=encabezados,
            json={
                "nombre": "Ana",
                "apellido": "Pérez",
                "fecha_nacimiento": "2018-07-05",
                "grupo_id": tiburones_manana,
                "familia_id": familia,
            },
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["familia"] == {
            "id": familia,
            "etiqueta": "Pérez – Ana",
            "categoria": "empleado",
        }
        assert cuerpo["inscripcion"]["grupo_id"] == tiburones_manana
        assert cuerpo["inscripcion"]["temporada_id"] == vigente
        # No se creo otra familia ni otra persona; si el alumno y su inscripcion.
        despues = _conteos(sesion)
        assert {t: despues[t] - antes[t] for t in TABLAS} == {
            "familia": 0,
            "persona": 0,
            "familia_persona": 0,
            "alumno": 1,
            "inscripcion": 1,
        }
        familia_de_ana = sesion.execute(
            text("SELECT familia_id FROM alumno WHERE id = :a"), {"a": cuerpo["id"]}
        ).scalar_one()
        assert familia_de_ana == familia
        # AND sigue teniendo a María como tutora y ningún otro vínculo.
        assert _vinculos(sesion, familia) == [(maria, True, True)]
        categoria = sesion.execute(
            text("SELECT categoria FROM familia WHERE id = :f"), {"f": familia}
        ).scalar_one()
        assert categoria == "empleado"

    def test_mandar_categoria_con_una_familia_existente_responde_422_y_no_la_cambia(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Intento de cambiar la categoría en el alta
        familia, _ = _familia_perez_ana(sesion)
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=profesor_de_delfines,
            json={
                "nombre": "Tomás",
                "apellido": "Pérez",
                "fecha_nacimiento": "2020-05-05",
                "grupo_id": delfines_manana,
                "familia_id": familia,
                "categoria": "socio",
                "personas": [],
            },
        )

        _afirmar_error(
            respuesta,
            ("categoria",),
            "La categoría de una familia existente no se cambia en el alta.",
        )
        assert _conteos(sesion) == antes
        categoria = sesion.execute(
            text("SELECT categoria FROM familia WHERE id = :f"), {"f": familia}
        ).scalar_one()
        assert categoria == "empleado"

    def test_una_familia_que_no_existe_responde_422_en_familia_id(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Familia que no existe
        _familia_perez_ana(sesion)
        inexistente = _id_inexistente(sesion, "familia")
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, categoria=OMITIR, familia_id=inexistente, personas=[]),
        )

        _afirmar_error(respuesta, ("familia_id",), "La familia no existe.")
        assert _conteos(sesion) == antes

    def test_reutilizar_una_persona_ya_vinculada_a_la_familia_responde_422_y_no_crea_el_alumno(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Persona ya vinculada a la familia
        familia, maria = _familia_perez_ana(sesion)
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(
                delfines_manana,
                nombre="Tomás",
                fecha_nacimiento="2020-05-05",
                categoria=OMITIR,
                familia_id=familia,
                personas=[{"persona_id": maria, "es_tutor": True}],
            ),
        )

        _afirmar_error(
            respuesta, ("personas", 0, "persona_id"), "Esa persona ya está vinculada a la familia."
        )
        assert _conteos(sesion) == antes
        assert _vinculos(sesion, familia) == [(maria, True, True)]


# --- Requirement: Personas en el alta --------------------------------------


class TestPersonasEnElAlta:
    def test_reutilizar_una_persona_de_otra_familia_la_vincula_a_las_dos_sin_duplicarla(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Reutilizar una persona de otra familia
        familia_perez, maria = _familia_perez_ana(sesion)
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
                personas=[{"persona_id": maria, "es_tutor": True}],
            ),
        )

        assert respuesta.status_code == 201, respuesta.text
        familia_gomez = respuesta.json()["familia"]["id"]
        assert familia_gomez != familia_perez
        assert respuesta.json()["familia"]["categoria"] == "socio"
        # AND María vinculada a las dos familias.
        familias_de_maria = sesion.execute(
            text(
                "SELECT familia_id FROM familia_persona WHERE persona_id = :p ORDER BY familia_id"
            ),
            {"p": maria},
        ).scalars()
        assert sorted(familias_de_maria) == sorted([familia_perez, familia_gomez])
        assert _vinculos(sesion, familia_gomez) == [(maria, True, True)]
        # AND sigue habiendo una sola persona con su DNI.
        con_su_dni = sesion.execute(
            text("SELECT count(*) FROM persona WHERE dni = '30111222'")
        ).scalar_one()
        assert con_su_dni == 1
        assert _conteos(sesion)["persona"] == antes["persona"]

    def test_una_persona_nueva_con_un_dni_ya_cargado_con_puntos_responde_422_y_no_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Persona nueva con un DNI ya cargado
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
                personas=[_maria_nueva(dni="30.111.222")],
            ),
        )

        _afirmar_error(
            respuesta,
            ("personas", 0, "dni"),
            "Ya hay una persona con ese DNI. Buscala por DNI para reutilizarla.",
        )
        assert _conteos(sesion) == antes

    def test_la_misma_persona_dos_veces_responde_422_en_la_segunda(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: La misma persona dos veces
        _, maria = _familia_perez_ana(sesion)
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
                    {"persona_id": maria, "es_tutor": True},
                    {"persona_id": maria, "es_tutor": True},
                ],
            ),
        )

        _afirmar_error(respuesta, ("personas", 1, "persona_id"), "Esa persona ya está en el alta.")
        assert _conteos(sesion) == antes

    def test_una_persona_que_no_existe_responde_422_en_su_persona_id(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Persona que no existe
        _familia_perez_ana(sesion)
        inexistente = _id_inexistente(sesion, "persona")
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[{"persona_id": inexistente, "es_tutor": True}]),
        )

        _afirmar_error(respuesta, ("personas", 0, "persona_id"), "La persona no existe.")
        assert _conteos(sesion) == antes

    def test_una_persona_nueva_sin_telefono_responde_422_en_su_telefono(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Persona nueva sin teléfono
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[_maria_nueva(telefono=OMITIR)]),
        )

        _afirmar_error(respuesta, ("personas", 0, "telefono"))
        assert _conteos(sesion) == antes

    def test_un_dni_de_15_caracteres_se_acepta(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: DNI de 15 caracteres
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[_maria_nueva(dni="123456789012345")]),
        )

        assert respuesta.status_code == 201, respuesta.text
        guardadas = sesion.execute(
            text("SELECT count(*) FROM persona WHERE dni = '123456789012345'")
        ).scalar_one()
        assert guardadas == 1

    def test_un_dni_de_16_caracteres_responde_422_en_su_dni(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: DNI de 16 caracteres
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, personas=[_maria_nueva(dni="1234567890123456")]),
        )

        _afirmar_error(respuesta, ("personas", 0, "dni"))
        assert _conteos(sesion) == antes


# --- Requirement: Datos del alumno en el alta ------------------------------


class TestDatosDelAlumno:
    def test_un_nombre_de_80_caracteres_se_acepta(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Nombre de 80 caracteres
        nombre = "J" * 80

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, nombre=nombre)
        )

        assert respuesta.status_code == 201, respuesta.text
        guardado = sesion.execute(
            text("SELECT nombre FROM alumno WHERE id = :a"), {"a": respuesta.json()["id"]}
        ).scalar_one()
        assert guardado == nombre

    def test_un_nombre_de_81_caracteres_responde_422_en_nombre(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Nombre de 81 caracteres
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, nombre="J" * 81)
        )

        _afirmar_error(respuesta, ("nombre",))
        assert _conteos(sesion) == antes

    def test_un_alumno_nacido_hoy_se_acepta(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Nacido hoy
        hoy = date.today()

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, fecha_nacimiento=hoy.isoformat()),
        )

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["fecha_nacimiento"] == hoy.isoformat()

    def test_un_alumno_nacido_manana_responde_422_en_fecha_nacimiento(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Nacido mañana
        manana = date.today() + timedelta(days=1)
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, fecha_nacimiento=manana.isoformat()),
        )

        _afirmar_error(
            respuesta, ("fecha_nacimiento",), "La fecha de nacimiento no puede ser posterior a hoy."
        )
        assert _conteos(sesion) == antes


# --- Requirement: El grupo del alta ----------------------------------------


class TestGrupoDelAlta:
    def test_un_grupo_fuera_del_rango_de_nacimiento_igual_inscribe(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        tiburones_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo fuera del rango de nacimiento
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(
                tiburones_manana,
                nombre="Lucía",
                apellido="Gómez",
                fecha_nacimiento="2020-02-02",
                personas=[_maria_nueva(apellido="Gómez")],
            ),
        )

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["inscripcion"] == {
            "grupo_id": tiburones_manana,
            "grupo_nombre": "Tiburones",
            "turno": "manana",
            "temporada_id": vigente,
        }
        grupo = sesion.execute(
            text("SELECT grupo_id FROM inscripcion WHERE alumno_id = :a"),
            {"a": respuesta.json()["id"]},
        ).scalar_one()
        assert grupo == tiburones_manana

    def test_un_grupo_inactivo_responde_422_en_grupo_id(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo inactivo
        pulpos = _insertar_grupo(
            sesion, vigente, "Pulpos", "manana", date(2020, 1, 1), date(2021, 12, 31), activo=False
        )
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, headers=coordinador, json=_cuerpo(pulpos))

        _afirmar_error(respuesta, ("grupo_id",), "El grupo no está activo.")
        assert _conteos(sesion) == antes

    def test_un_grupo_de_la_temporada_cerrada_responde_422_en_grupo_id(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo de una temporada cerrada
        cerrada = _crear_temporada(
            sesion, "2025-26", EstadoTemporada.CERRADA, date(2025, 12, 15), date(2026, 2, 28)
        )
        delfines_viejo = _insertar_grupo(
            sesion, cerrada, "Delfines", "manana", date(2019, 1, 1), date(2020, 12, 31)
        )
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_viejo))

        _afirmar_error(respuesta, ("grupo_id",), "El grupo no es de la temporada vigente.")
        assert _conteos(sesion) == antes

    def test_un_grupo_que_no_existe_responde_422_en_grupo_id(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo que no existe
        inexistente = _id_inexistente(sesion, "grupo")
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, headers=coordinador, json=_cuerpo(inexistente))

        _afirmar_error(respuesta, ("grupo_id",), "El grupo no existe.")
        assert _conteos(sesion) == antes


# --- Requirement: Quién puede dar de alta un alumno ------------------------


class TestQuienPuedeDarDeAlta:
    def test_el_profesor_inscribe_en_su_grupo(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Profesor en su grupo
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(delfines_manana)
        )

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["inscripcion"]["grupo_id"] == delfines_manana
        assert _conteos(sesion)["alumno"] == antes["alumno"] + 1

    def test_el_profesor_en_un_grupo_ajeno_recibe_403_y_no_se_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        tiburones_manana: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Profesor en un grupo ajeno
        # «Tiburones» tiene su propio profesor: no es un grupo sin dueño.
        otro = _crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        _asignar(sesion, tiburones_manana, otro)
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(tiburones_manana)
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert _conteos(sesion) == antes

        # Contraste: el mismo pedido en su grupo se acepta, asi que el 403 se
        # debio al grupo y no a otro dato del pedido.
        en_su_grupo = cliente.post(
            URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(delfines_manana)
        )
        assert en_su_grupo.status_code == 201, en_su_grupo.text

    def test_el_profesor_en_el_mismo_grupo_del_otro_turno_recibe_403(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        profesor_de_delfines: dict[str, str],
    ) -> None:
        # Scenario: Profesor en el mismo grupo del otro turno
        delfines_tarde = _insertar_grupo(
            sesion, vigente, "Delfines", "tarde", date(2020, 1, 1), date(2021, 12, 31)
        )
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=profesor_de_delfines, json=_cuerpo(delfines_tarde)
        )

        assert respuesta.status_code == 403, respuesta.text
        assert _conteos(sesion) == antes

    def test_sin_token_responde_401_y_no_se_crea_nada(
        self, cliente: TestClient, sesion: Session, delfines_manana: int
    ) -> None:
        # Scenario: Sin sesión
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, json=_cuerpo(delfines_manana))

        assert respuesta.status_code == 401, respuesta.text
        assert _conteos(sesion) == antes

    def test_con_el_cambio_de_contrasena_pendiente_responde_403_y_no_se_crea_nada(
        self, cliente: TestClient, sesion: Session, delfines_manana: int
    ) -> None:
        # Scenario: Con el cambio de contraseña pendiente
        _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR, debe_cambiar_password=True)
        encabezados = _ingresar(cliente, "coordi")
        antes = _conteos(sesion)

        respuesta = cliente.post(URL_ALUMNOS, headers=encabezados, json=_cuerpo(delfines_manana))

        assert respuesta.status_code == 403, respuesta.text
        assert _conteos(sesion) == antes
