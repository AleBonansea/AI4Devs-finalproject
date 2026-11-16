"""Capability `familias`: busquedas, Scenarios agregados por el pase
adversarial (change familias-y-alumnos, tarea 9.2).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/familias/spec.md`:
- «Buscar familias por apellido»: «Los comodines se buscan como texto».
- «Buscar una persona por DNI»: «DNI escrito con guiones».

La preparacion sigue a `familias/test_busquedas.py`.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import RolUsuario, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_FAMILIAS = "/api/v1/familias"
URL_PERSONAS = "/api/v1/personas"
CONTRASENA = "Verano2026"


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


def _crear_persona(sesion: Session, nombre: str, apellido: str, dni: str, telefono: str) -> int:
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


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


# --- Requirement: Buscar familias por apellido -----------------------------


class TestBuscarFamiliasHallazgos:
    def test_los_comodines_se_buscan_como_texto_y_no_encuentran_nada(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Los comodines se buscan como texto
        familia = _crear_familia(sesion, "empleado")
        _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))
        # Ningun alumno tiene `%` ni `_` en el apellido.
        con_comodin = sesion.execute(
            text(
                "SELECT count(*) FROM alumno "
                "WHERE strpos(apellido, '%') > 0 OR strpos(apellido, '_') > 0"
            )
        ).scalar_one()
        assert con_comodin == 0
        # La familia existe y se encuentra por su apellido: si `P%` o `P_rez`
        # se tomaran como patron, la encontrarian.
        por_texto = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": "Pérez"})
        assert por_texto.status_code == 200, por_texto.text
        assert [f["etiqueta"] for f in por_texto.json()] == ["Pérez – Ana"]

        # Llega como `apellido=P%25`.
        con_porcentaje = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": "P%"})
        con_guion_bajo = cliente.get(
            URL_FAMILIAS, headers=coordinador, params={"apellido": "P_rez"}
        )

        assert con_porcentaje.status_code == 200, con_porcentaje.text
        assert con_porcentaje.json() == []
        assert con_guion_bajo.status_code == 200, con_guion_bajo.text
        assert con_guion_bajo.json() == []


# --- Requirement: Buscar una persona por DNI -------------------------------


class TestBuscarPersonaHallazgos:
    def test_un_dni_escrito_con_guiones_encuentra_a_la_persona(
        self, cliente: TestClient, sesion: Session, coordinador: dict[str, str]
    ) -> None:
        # Scenario: DNI escrito con guiones
        familia = _crear_familia(sesion, "empleado")
        _crear_alumno(sesion, familia, "Ana", "Pérez", date(2018, 7, 5))
        maria = _crear_persona(sesion, "María", "Pérez", "30111222", "3511234567")
        _vincular_tutor(sesion, familia, maria)
        # Otra persona con otro DNI: encontrarla no sale de que sea la unica.
        _crear_persona(sesion, "Raúl", "Gómez", "28999888", "3517654321")

        respuesta = cliente.get(URL_PERSONAS, headers=coordinador, params={"dni": "30-111-222"})

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["id"] == maria
