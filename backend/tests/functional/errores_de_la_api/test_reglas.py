"""Capability `errores-de-la-api`: rechazos de reglas del negocio
(change familias-y-alumnos, tarea 4.1).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/errores-de-la-api/spec.md`,
Requirement «Rechazos de reglas del negocio con la forma de validación»
(1 Scenario).

Se prueba por la API con `POST /api/v1/alumnos`. El estado se prepara con la
sesion del test, igual que `alumnos/test_alta.py`.
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_ALUMNOS = "/api/v1/alumnos"
CONTRASENA = "Verano2026"


def _crear_coordinador(sesion: Session) -> None:
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


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _crear_vigente(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def _grupo_inactivo(sesion: Session, temporada_id: int) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, 'Pulpos', 'manana', :d, :h, false) RETURNING id"
            ),
            {"t": temporada_id, "d": date(2020, 1, 1), "h": date(2021, 12, 31)},
        ).scalar_one()
    )


class TestRechazosDeReglasDelNegocio:
    def test_un_grupo_inactivo_responde_422_con_un_solo_error_de_regla_en_body_grupo_id(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Grupo inactivo
        pulpos = _grupo_inactivo(sesion, _crear_vigente(sesion))
        _crear_coordinador(sesion)
        encabezados = _ingresar(cliente, "coordi")

        # El resto del alta es valido: el unico motivo de rechazo es el grupo.
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=encabezados,
            json={
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": "2020-03-10",
                "grupo_id": pulpos,
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
            },
        )

        assert respuesta.status_code == 422, respuesta.text
        assert respuesta.json() == {
            "detail": [
                {
                    "loc": ["body", "grupo_id"],
                    "msg": "El grupo no está activo.",
                    "type": "regla_de_negocio",
                }
            ]
        }
