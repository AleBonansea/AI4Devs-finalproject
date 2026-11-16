"""Capability `cargos`: solo el Admin registra y simula cargos.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirement «Solo el Admin registra cargos», salvo «Coordinador pide las
opciones», que va con `GET /api/v1/cargos/opciones` en otra tarea.

Cada pedido lleva un «Abono» del Mes valido, con el tarifario completo: si
el cuerpo estuviera mal, un 422 podria tapar la falta del 403. «No se guarda
nada» se comprueba contando los cargos antes y despues.
"""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import RolUsuario, Usuario
from tests.functional.asistencia.preparacion import (
    CONTRASENA,
    asignar,
    crear_usuario,
    ingresar,
)
from tests.functional.cargos.preparacion import (
    CAMPOS_DE_MONTO,
    MENSAJE_SIN_PERMISO,
    URL_CARGOS,
    URL_SIMULACION,
    Hijo,
    Vigente,
    abono_mes,
    contar_cargos,
    descuentos_mes,
    familia_con_hijos,
    preparar_vigente,
    tarifa,
)


@dataclass(frozen=True)
class Estado:
    v: Vigente
    juan: Hijo


@pytest.fixture
def estado(sesion: Session) -> Estado:
    """Juan Perez, `empleado`, inscripto en «Delfines» manana, con la tarifa
    del Mes y el descuento de un hijo cargados: un Abono del Mes valido."""
    v = preparar_vigente(sesion)
    tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
    descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00"})
    _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
    return Estado(v=v, juan=juan)


def _sin_montos(cuerpo: object) -> None:
    """La respuesta no trae ningun monto ni porcentaje, en ningun nivel."""
    texto = str(cuerpo)
    for campo in CAMPOS_DE_MONTO:
        assert campo not in texto, f"La respuesta trae {campo}: {texto}"
    assert "90000" not in texto and "100000" not in texto, texto


class TestSoloElAdminRegistraCargos:
    def test_el_coordinador_recibe_403_y_no_se_guarda_ningun_cargo(
        self, cliente: TestClient, sesion: Session, estado: Estado
    ) -> None:
        # Scenario: Coordinador registra un cargo
        crear_usuario(sesion, "lrodriguez", RolUsuario.COORDINADOR)
        encabezados = ingresar(cliente, "lrodriguez")
        antes = contar_cargos(sesion)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono_mes(estado.v, estado.juan)
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        assert contar_cargos(sesion) == antes

    def test_el_profesor_del_grupo_del_alumno_recibe_403_y_no_se_guarda_ningun_cargo(
        self, cliente: TestClient, sesion: Session, estado: Estado
    ) -> None:
        # Scenario: Profesor registra un cargo a un alumno de su grupo
        profesor = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, estado.v.delfines, profesor)
        encabezados = ingresar(cliente, "jperez")
        antes = contar_cargos(sesion)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono_mes(estado.v, estado.juan)
        )

        assert respuesta.status_code == 403, respuesta.text
        assert contar_cargos(sesion) == antes

    def test_el_profesor_que_simula_recibe_403_sin_ningun_monto(
        self, cliente: TestClient, sesion: Session, estado: Estado
    ) -> None:
        # Scenario: Profesor simula un cargo
        profesor = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, estado.v.delfines, profesor)
        encabezados = ingresar(cliente, "jperez")

        respuesta = cliente.post(
            URL_SIMULACION, headers=encabezados, json=abono_mes(estado.v, estado.juan)
        )

        assert respuesta.status_code == 403, respuesta.text
        _sin_montos(respuesta.json())

    def test_sin_token_responde_401_y_no_se_guarda_ningun_cargo(
        self, cliente: TestClient, sesion: Session, estado: Estado
    ) -> None:
        # Scenario: Sin sesión
        antes = contar_cargos(sesion)

        respuesta = cliente.post(URL_CARGOS, json=abono_mes(estado.v, estado.juan))

        assert respuesta.status_code == 401, respuesta.text
        assert contar_cargos(sesion) == antes

    def test_el_admin_con_el_cambio_de_contrasena_pendiente_recibe_403_y_no_se_guarda_nada(
        self, cliente: TestClient, sesion: Session, estado: Estado
    ) -> None:
        # Scenario: Admin con el cambio de contraseña pendiente
        sesion.add(
            Usuario(
                username="admin2",
                password_hash=hashear(CONTRASENA),
                debe_cambiar_password=True,
                intentos_fallidos=0,
                nombre="Usuario",
                apellido="Admin2",
                rol=RolUsuario.ADMIN,
                activo=True,
            )
        )
        sesion.flush()
        encabezados = ingresar(cliente, "admin2")
        antes = contar_cargos(sesion)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono_mes(estado.v, estado.juan)
        )

        assert respuesta.status_code == 403, respuesta.text
        assert contar_cargos(sesion) == antes
