"""Capability `errores-de-la-api`: caracteres de control en los textos
(change familias-y-alumnos, tarea 9.2, hallazgo del pase adversarial).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/errores-de-la-api/spec.md`,
Requirement «Caracteres de control en los textos» (4 Scenarios).

Cada pedido es valido salvo el caracter NUL, asi el 422 se debe a el: se
afirma que el unico error del `detail` es el del campo del Scenario, con el
`msg` exacto. Un 500 (el NUL llegando a Postgres) hace fallar el test.

La preparacion sigue a `alumnos/test_alta.py` y `familias/test_busquedas.py`:
usuarios y temporada con el ORM, grupo, familia y personas con SQL crudo, y
tokens del login real.
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
URL_ALUMNOS = "/api/v1/alumnos"
URL_FAMILIAS = "/api/v1/familias"
URL_PERSONAS = "/api/v1/personas"
CONTRASENA = "Verano2026"

MENSAJE_CONTROL = "No puede tener caracteres de control."

TABLAS = ("familia", "persona", "familia_persona", "alumno", "inscripcion")


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


def _crear_familia_perez_ana_con_maria(sesion: Session) -> None:
    """La familia `Pérez – Ana` con María Pérez (DNI 30111222) como tutora."""
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


def _conteos(sesion: Session) -> dict[str, int]:
    return {
        tabla: int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())
        for tabla in TABLAS
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


def _loc_sin_origen(error: dict[str, Any]) -> list[Any]:
    """El `loc` sin el origen inicial (`body` o `query`)."""
    loc = list(error["loc"])
    if loc and loc[0] in ("body", "query"):
        loc = loc[1:]
    return loc


def _afirmar_unico_error(respuesta: Any, campo: list[Any], msg: str) -> None:
    """422 con un unico error, en `campo`, con `msg` exacto."""
    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    assert [_loc_sin_origen(e) for e in detalle] == [campo], respuesta.text
    assert [e["msg"] for e in detalle] == [msg], respuesta.text


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def delfines_manana(sesion: Session) -> int:
    """«Delfines» mañana de la temporada vigente 2026-27."""
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, 'Delfines', 'manana', :d, :h, true) RETURNING id"
            ),
            {"t": temporada.id, "d": date(2020, 1, 1), "h": date(2021, 12, 31)},
        ).scalar_one()
    )


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


# --- Requirement: Caracteres de control en los textos ----------------------


class TestCaracteresDeControl:
    def test_un_nul_en_el_nombre_del_alumno_responde_422_en_nombre_y_no_crea_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Carácter NUL en el nombre del alumno
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, nombre="Ju\u0000an")
        )

        _afirmar_unico_error(respuesta, ["nombre"], MENSAJE_CONTROL)
        # AND no se crea nada.
        assert _conteos(sesion) == antes

    def test_un_nul_en_el_telefono_de_una_persona_responde_422_en_su_telefono(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Carácter NUL en el teléfono de una persona
        antes = _conteos(sesion)
        persona = {
            "nombre": "María",
            "apellido": "Pérez",
            "telefono": "351\u00001234",
            "dni": "30111222",
            "es_tutor": True,
        }

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, personas=[persona])
        )

        _afirmar_unico_error(respuesta, ["personas", 0, "telefono"], MENSAJE_CONTROL)
        assert _conteos(sesion) == antes

    def test_un_nul_en_la_busqueda_de_familias_responde_422_en_apellido(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Carácter NUL en la búsqueda de familias
        _crear_familia_perez_ana_con_maria(sesion)

        # Llega como `apellido=P%00e`: el byte NUL real en la direccion.
        respuesta = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": "P\x00e"})

        _afirmar_unico_error(respuesta, ["apellido"], MENSAJE_CONTROL)

    def test_un_nul_en_la_busqueda_por_dni_responde_422_en_dni(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Carácter NUL en la búsqueda por DNI
        _crear_familia_perez_ana_con_maria(sesion)

        # Llega como `dni=301%0011222`.
        respuesta = cliente.get(URL_PERSONAS, headers=coordinador, params={"dni": "301\x0011222"})

        _afirmar_unico_error(respuesta, ["dni"], MENSAJE_CONTROL)
