"""Capability `familias`: busquedas por la API (change familias-y-alumnos, tarea 3.1).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/familias/spec.md`:
- Requirement «Buscar familias por apellido» (9 Scenarios):
  `GET /api/v1/familias?apellido=`.
- Requirement «Buscar una persona por DNI» (5 Scenarios):
  `GET /api/v1/personas?dni=`.

Se prueba por la API. El estado se prepara con la sesion del test: usuarios y
temporada con el ORM, y familias, alumnos, personas, grupos e inscripciones
con SQL crudo sobre los nombres del modelo de datos, igual que
`test_familias_esquema.py` y `grupos/test_listar_grupos.py`. Los tokens salen
del login real.

El DNI se guarda en la base ya normalizado (`30111222`): la normalizacion de
la que habla la spec es la del texto pedido.
"""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_FAMILIAS = "/api/v1/familias"
URL_PERSONAS = "/api/v1/personas"
CONTRASENA = "Verano2026"

CAMPOS_DE_LA_FAMILIA = {"id", "etiqueta", "categoria"}
CAMPOS_DE_LA_PERSONA = {"id", "nombre", "apellido"}

MENSAJE_SIN_DNI = "No hay ninguna persona con ese DNI."
MENSAJE_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar."


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


def _crear_temporada(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def _crear_grupo(sesion: Session, temporada_id: int, nombre: str, turno: str) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo "
                "(temporada_id, nombre, turno, nacimiento_desde, nacimiento_hasta) "
                "VALUES (:t, :n, :tu, :d, :h) RETURNING id"
            ),
            {
                "t": temporada_id,
                "n": nombre,
                "tu": turno,
                "d": date(2017, 1, 1),
                "h": date(2021, 12, 31),
            },
        ).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def _inscribir(
    sesion: Session,
    alumno_id: int,
    grupo_id: int,
    temporada_id: int,
    turno: str,
    creado_por: int,
) -> None:
    sesion.execute(
        text(
            "INSERT INTO inscripcion (alumno_id, grupo_id, temporada_id, turno, creado_por) "
            "VALUES (:a, :g, :t, :tu, :c)"
        ),
        {"a": alumno_id, "g": grupo_id, "t": temporada_id, "tu": turno, "c": creado_por},
    )


def _crear_familia(sesion: Session, categoria: str = "empleado") -> int:
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


def _familia_perez_ana(sesion: Session, categoria: str = "empleado") -> tuple[int, int]:
    """La familia `Pérez – Ana`: Ana Pérez nacida el 2018-07-05. Devuelve
    (familia, alumna)."""
    familia = _crear_familia(sesion, categoria)
    ana = _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))
    return familia, ana


def _familia_gomez_lucia(sesion: Session) -> int:
    """Una familia que no coincide con `Pérez` ni con `Mar`."""
    familia = _crear_familia(sesion, "socio")
    _crear_alumno(sesion, familia, "Lucía", "Gómez", date(2019, 2, 2))
    return familia


def _crear_persona(
    sesion: Session,
    nombre: str,
    apellido: str,
    dni: str | None,
    telefono: str = "3511234567",
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


def _maria_perez(sesion: Session) -> int:
    """María Pérez, teléfono 3511234567, DNI 30111222, tutora de `Pérez – Ana`.
    Se suma otra persona con otro DNI, para que encontrarla no salga gratis
    de que sea la unica."""
    familia, _ = _familia_perez_ana(sesion)
    maria = _crear_persona(sesion, "María", "Pérez", "30111222", telefono="3511234567")
    _vincular_tutor(sesion, familia, maria)
    raul = _crear_persona(sesion, "Raúl", "Gómez", "28999888", telefono="3517654321")
    _vincular_tutor(sesion, _familia_gomez_lucia(sesion), raul)
    return maria


def _buscar_familias(
    cliente: TestClient, encabezados: dict[str, str], apellido: str
) -> list[dict[str, Any]]:
    respuesta = cliente.get(URL_FAMILIAS, headers=encabezados, params={"apellido": apellido})
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert isinstance(cuerpo, list)
    return cuerpo


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


# --- Requirement: Buscar familias por apellido -----------------------------


class TestBuscarFamiliasPorApellido:
    def test_buscar_por_el_apellido_del_hijo_mayor_trae_esa_familia_con_etiqueta_y_categoria(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Búsqueda por el apellido del hijo mayor
        familia, _ = _familia_perez_ana(sesion, "empleado")
        # Contraste: una familia que no coincide y otra cuyo apellido contiene
        # «pér» pero no empieza con eso.
        _familia_gomez_lucia(sesion)
        otra = _crear_familia(sesion, "socio")
        _crear_alumno(sesion, otra, "Bruno", "Ampérez", date(2019, 1, 1))

        familias = _buscar_familias(cliente, coordinador, "pér")

        assert familias == [{"id": familia, "etiqueta": "Pérez – Ana", "categoria": "empleado"}]

    def test_buscar_por_el_apellido_de_un_medio_hermano_incluye_la_familia(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Búsqueda por el apellido de un medio hermano
        familia, _ = _familia_perez_ana(sesion)
        _crear_alumno(sesion, familia, "Tomás", "Gómez", date(2019, 11, 20))
        # Contraste: una familia sin ningun Gómez no viene.
        sin_gomez = _crear_familia(sesion, "socio")
        _crear_alumno(sesion, sin_gomez, "Juan", "Ruiz", date(2019, 3, 3))
        _crear_usuario(sesion, "admin1", RolUsuario.ADMIN)

        familias = _buscar_familias(cliente, _ingresar(cliente, "admin1"), "Gómez")

        encontradas = [f for f in familias if f["id"] == familia]
        assert len(encontradas) == 1, familias
        assert encontradas[0]["etiqueta"] == "Pérez – Ana"
        assert sin_gomez not in [f["id"] for f in familias]

    def test_el_profesor_encuentra_una_familia_ajena_y_solo_ve_id_etiqueta_y_categoria(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un Profesor encuentra una familia sin hijos en sus grupos
        temporada = _crear_temporada(sesion)
        delfines = _crear_grupo(sesion, temporada, "Delfines", "manana")
        tiburones = _crear_grupo(sesion, temporada, "Tiburones", "manana")
        profesor = _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        _asignar(sesion, delfines, profesor)
        # Tiburones tiene otro profesor: el Profesor del token no tiene nada
        # que ver con la familia.
        otro = _crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        _asignar(sesion, tiburones, otro)

        familia, ana = _familia_perez_ana(sesion)
        tomas = _crear_alumno(sesion, familia, "Tomás", "Pérez", date(2019, 11, 20))
        _inscribir(sesion, ana, tiburones, temporada, "manana", otro)
        _inscribir(sesion, tomas, tiburones, temporada, "manana", otro)
        # La familia no tiene ninguna inscripcion en «Delfines».
        en_delfines = sesion.execute(
            text(
                "SELECT count(*) FROM inscripcion i JOIN alumno a ON a.id = i.alumno_id "
                "WHERE a.familia_id = :f AND i.grupo_id = :g"
            ),
            {"f": familia, "g": delfines},
        ).scalar_one()
        assert en_delfines == 0

        respuesta = cliente.get(
            URL_FAMILIAS, headers=_ingresar(cliente, "jperez"), params={"apellido": "Pérez"}
        )

        assert respuesta.status_code == 200, respuesta.text
        familias = respuesta.json()
        assert familia in [f["id"] for f in familias]
        # AND cada elemento tiene exactamente id, etiqueta y categoria.
        assert familias, familias
        for f in familias:
            assert set(f) == CAMPOS_DE_LA_FAMILIA, f

    def test_un_texto_de_dos_caracteres_responde_200(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Texto de dos caracteres
        familia, _ = _familia_perez_ana(sesion)

        respuesta = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": "Pé"})

        assert respuesta.status_code == 200, respuesta.text
        assert familia in [f["id"] for f in respuesta.json()]

    def test_un_texto_de_un_caracter_entre_espacios_responde_422(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Texto de un carácter
        _familia_perez_ana(sesion)

        # Llega como `apellido=%20P%20`: tres caracteres, uno despues de recortar.
        respuesta = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": " P "})

        assert respuesta.status_code == 422, respuesta.text

    def test_con_mas_de_20_coincidencias_trae_exactamente_20_ordenadas_por_etiqueta(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Más de 20 coincidencias
        # Nombres ASCII con inicial distinta: el orden por etiqueta no depende
        # de la intercalacion de la base. Se insertan en un orden que no es el
        # alfabetico, para que el orden de la respuesta no salga del id.
        nombres = [
            "Ulises", "Carla", "Pablo", "Bruno", "Tania", "Hugo", "Ramiro",
            "Diego", "Olga", "Ezequiel", "Nora", "Federico", "Silvia", "Gabriel",
            "Ines", "Quique", "Julia", "Mirta", "Karina", "Lucas",
        ]  # fmt: skip
        assert len(nombres) == 20
        etiquetas: dict[str, int] = {}
        for nombre in nombres:
            familia = _crear_familia(sesion, "no_socio")
            _crear_alumno(sesion, familia, nombre, "Martínez", date(2019, 4, 4))
            etiquetas[f"Martínez – {nombre}"] = familia
        _familia_gomez_lucia(sesion)

        # Lado de adentro: con 20 coincidencias vienen las 20.
        familias = _buscar_familias(cliente, coordinador, "Mar")
        assert [f["etiqueta"] for f in familias] == sorted(etiquetas)
        assert [f["id"] for f in familias] == [etiquetas[e] for e in sorted(etiquetas)]

        # Lado de afuera: la familia 21 se inserta ultima pero va primera por
        # etiqueta. Tiene que entrar y desplazar a la ultima por etiqueta.
        abel = _crear_familia(sesion, "no_socio")
        _crear_alumno(sesion, abel, "Abel", "Martínez", date(2019, 4, 4))
        etiquetas["Martínez – Abel"] = abel
        assert len(etiquetas) == 21

        familias = _buscar_familias(cliente, coordinador, "Mar")

        assert len(familias) == 20
        esperadas = sorted(etiquetas)[:20]
        assert [f["etiqueta"] for f in familias] == esperadas
        assert [f["id"] for f in familias] == [etiquetas[e] for e in esperadas]
        assert etiquetas["Martínez – Ulises"] not in [f["id"] for f in familias]

    def test_sin_coincidencias_responde_200_con_una_lista_vacia(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Sin coincidencias
        # Hay familias: la lista vacia no sale de que no exista ninguna.
        _familia_perez_ana(sesion)
        _familia_gomez_lucia(sesion)

        respuesta = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": "Zzz"})

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json() == []

    def test_sin_token_buscar_familias_responde_401(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Sin sesión (familias)
        _familia_perez_ana(sesion)

        respuesta = cliente.get(URL_FAMILIAS, params={"apellido": "Pérez"})

        assert respuesta.status_code == 401, respuesta.text

    def test_con_el_cambio_de_contrasena_pendiente_buscar_familias_responde_403(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Con el cambio de contraseña pendiente
        _familia_perez_ana(sesion)
        _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR, debe_cambiar_password=True)

        respuesta = cliente.get(
            URL_FAMILIAS, headers=_ingresar(cliente, "jperez"), params={"apellido": "Pérez"}
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_CAMBIO_PENDIENTE


# --- Requirement: Buscar una persona por DNI -------------------------------


class TestBuscarPersonaPorDni:
    def test_un_dni_que_existe_devuelve_solo_id_nombre_y_apellido_de_la_persona(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: DNI que existe
        maria = _maria_perez(sesion)
        _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)

        respuesta = cliente.get(
            URL_PERSONAS, headers=_ingresar(cliente, "jperez"), params={"dni": "30111222"}
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        # AND exactamente esos tres campos: ni teléfono, ni DNI, ni familias.
        assert set(cuerpo) == CAMPOS_DE_LA_PERSONA
        assert cuerpo == {"id": maria, "nombre": "María", "apellido": "Pérez"}

    def test_un_dni_escrito_con_puntos_encuentra_a_la_persona(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: DNI escrito con puntos
        maria = _maria_perez(sesion)

        respuesta = cliente.get(URL_PERSONAS, headers=coordinador, params={"dni": "30.111.222"})

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["id"] == maria

    def test_un_dni_incompleto_responde_404_con_el_mensaje(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: DNI incompleto
        _maria_perez(sesion)

        respuesta = cliente.get(URL_PERSONAS, headers=coordinador, params={"dni": "3011122"})

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_DNI

    def test_un_dni_vacio_responde_422(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: DNI vacío
        _maria_perez(sesion)

        # Llega como `dni=%20`.
        respuesta = cliente.get(URL_PERSONAS, headers=coordinador, params={"dni": " "})

        assert respuesta.status_code == 422, respuesta.text

    def test_sin_token_buscar_una_persona_responde_401(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Sin sesión (personas)
        _maria_perez(sesion)

        respuesta = cliente.get(URL_PERSONAS, params={"dni": "30111222"})

        assert respuesta.status_code == 401, respuesta.text
