"""Capability `cuenta-corriente`: solo el Admin ve la cuenta corriente
(change cuenta-corriente, tarea 3.1).

Un test por Scenario del Requirement «Solo el Admin ve la cuenta corriente»,
en `openspec/changes/cuenta-corriente/specs/cuenta-corriente/spec.md`.

Endpoint: `GET /api/v1/familias/{familia_id}/cuenta-corriente`. El 403 va
antes de buscar la familia: un Profesor con un id inexistente recibe 403 y
no 404, asi no sabe si la familia existe.

En cada 403 la familia tiene cargos y pagos de verdad, para que «no trae
ningun monto» signifique algo: el contraste del Admin sobre la misma familia
comprueba que si los hay.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    asignar,
    crear_alumno,
    crear_familia,
    crear_usuario,
    ingresar,
    inscribir,
    insertar_grupo,
)
from tests.functional.cuenta_corriente.preparacion import (
    ID_INEXISTENTE,
    MENSAJE_SIN_PERMISO,
    pedir,
    pedir_200,
)
from tests.functional.pagos.preparacion_api import (
    Perez,
    admin,
    insertar_abono_mes,
    insertar_pago_previo,
    preparar_perez,
)

# Montos de la preparacion: ninguno puede aparecer en un 403.
MONTOS_DE_LA_FAMILIA = ("85000", "30000", "55000")


def _perez_con_cargos(sesion: Session) -> Perez:
    """«Pérez – Ana» con el Abono del Mes de Juan (85000.00) y un pago de 30000.00."""
    p = preparar_perez(sesion)
    abono = insertar_abono_mes(sesion, p)
    insertar_pago_previo(sesion, abono, "30000.00", p.admin)
    return p


def _sin_montos(texto: str) -> None:
    for monto in MONTOS_DE_LA_FAMILIA:
        assert monto not in texto, texto
    assert "cargos" not in texto
    assert "saldo" not in texto


class TestSoloElAdminVeLaCuentaCorriente:
    def test_la_profesora_de_otro_grupo_recibe_403_sin_ningun_cargo_ni_monto(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Profesor de otro grupo
        # `cfernandez` esta asignada solo a «Pulpos» tarde, con Lucía Gómez y
        # sin ningun hijo de la familia Pérez.
        p = _perez_con_cargos(sesion)
        pulpos = insertar_grupo(sesion, p.temporada, "Pulpos", "tarde")
        gomez = crear_familia(sesion, "socio")
        lucia = crear_alumno(sesion, "Lucía", "Gómez", familia_id=gomez)
        inscribir(sesion, lucia, pulpos, p.temporada, "tarde", p.admin)
        cfernandez = crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        asignar(sesion, pulpos, cfernandez)

        respuesta = pedir(cliente, ingresar(cliente, "cfernandez"), p.familia)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        _sin_montos(respuesta.text)

        # Contraste: el Admin con la misma familia si ve el cargo y su saldo.
        del_admin = pedir_200(cliente, admin(cliente), p.familia)
        assert del_admin["saldo_pendiente"] == "55000.00"

    def test_el_profesor_del_grupo_de_un_hijo_recibe_403(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Profesor del grupo de un hijo
        p = _perez_con_cargos(sesion)  # Juan inscripto en «Delfines» manana
        jperez = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, p.delfines, jperez)

        respuesta = pedir(cliente, ingresar(cliente, "jperez"), p.familia)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        _sin_montos(respuesta.text)

    def test_el_profesor_con_una_familia_que_no_existe_recibe_403_y_no_404(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Profesor con una familia que no existe
        p = _perez_con_cargos(sesion)
        assert p.familia != ID_INEXISTENTE
        jperez = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, p.delfines, jperez)

        respuesta = pedir(cliente, ingresar(cliente, "jperez"), ID_INEXISTENTE)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO

    def test_el_coordinador_recibe_403(self, cliente: TestClient, sesion: Session) -> None:
        # Scenario: Coordinador
        p = _perez_con_cargos(sesion)
        crear_usuario(sesion, "lrodriguez", RolUsuario.COORDINADOR)

        respuesta = pedir(cliente, ingresar(cliente, "lrodriguez"), p.familia)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        _sin_montos(respuesta.text)

    def test_sin_sesion_responde_401(self, cliente: TestClient, sesion: Session) -> None:
        # Scenario: Sin sesión
        p = _perez_con_cargos(sesion)

        respuesta = pedir(cliente, None, p.familia)

        assert respuesta.status_code == 401, respuesta.text
        _sin_montos(respuesta.text)
