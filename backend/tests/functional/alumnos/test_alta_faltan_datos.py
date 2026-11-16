"""Capability `alumnos`: alta con varios datos minimos faltantes
(change familias-y-alumnos, tarea 4.2).

Un test para el Scenario «Faltan varios datos mínimos» del Requirement
«Datos del alumno en el alta» de
`openspec/changes/familias-y-alumnos/specs/alumnos/spec.md`.

Se prueba por la API con un Coordinador, igual que `test_alta.py`. «No se crea
nada» se comprueba contando las filas de las cinco tablas del alta antes y
despues, con SQL desde la sesion del test.
"""

from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_ALUMNOS = "/api/v1/alumnos"
CONTRASENA = "Verano2026"

TABLAS = ("familia", "persona", "familia_persona", "alumno", "inscripcion")


def _preparar(sesion: Session) -> None:
    """Una temporada vigente con un grupo activo y un Coordinador: que el alta
    falle solo puede deberse a lo que le falta al cuerpo."""
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.add(
        Usuario(
            username="coordi",
            password_hash=hashear(CONTRASENA),
            debe_cambiar_password=False,
            intentos_fallidos=0,
            nombre="Juan",
            apellido="Perez",
            rol=RolUsuario.COORDINADOR,
            activo=True,
        )
    )
    sesion.flush()
    sesion.execute(
        text(
            "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
            "nacimiento_hasta, activo) "
            "VALUES (:t, 'Delfines', 'manana', :d, :h, true)"
        ),
        {"t": temporada.id, "d": date(2020, 1, 1), "h": date(2021, 12, 31)},
    )


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _conteos(sesion: Session) -> dict[str, int]:
    return {
        tabla: int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())
        for tabla in TABLAS
    }


def _errores_en(respuesta: Any, campo: str) -> list[dict[str, Any]]:
    """Los errores de `detail` cuyo `loc` termina en `campo`."""
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    return [e for e in detalle if e["loc"] and e["loc"][-1] == campo]


class TestDatosDelAlumnoFaltanVarios:
    def test_sin_fecha_ni_grupo_responde_422_con_un_obligatorio_en_cada_uno_y_no_crea_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Faltan varios datos mínimos
        _preparar(sesion)
        coordinador = _ingresar(cliente, "coordi")
        antes = _conteos(sesion)

        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json={"nombre": "Juan", "apellido": "Pérez"}
        )

        assert respuesta.status_code == 422, respuesta.text
        for campo in ("fecha_nacimiento", "grupo_id"):
            errores = _errores_en(respuesta, campo)
            assert [e["msg"] for e in errores] == ["Este dato es obligatorio."], respuesta.text
        # AND no se crea nada.
        assert _conteos(sesion) == antes
