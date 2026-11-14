"""Capability `tesoreria`: cada pago escribe su ingreso (change
cuenta-corriente, tarea 2.1).

Un test por Scenario de
`openspec/changes/cuenta-corriente/specs/tesoreria/spec.md`, Requirement
«Cada pago escribe su ingreso».

Los pagos se registran por la API (`POST /api/v1/cargos/{cargo_id}/pagos`) y
la tesoreria se lee de la base, porque todavia no tiene endpoints. Montos como
`Decimal` exacto.
"""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import crear_usuario, ingresar
from tests.functional.pagos.preparacion import es_decimal_exacto
from tests.functional.pagos.preparacion_api import (
    admin,
    contar_movimientos,
    contar_pagos,
    cuerpo_pago,
    insertar_abono_mes,
    insertar_pago_previo,
    movimientos,
    pagar,
    pagar_201,
    preparar_perez,
)


class TestCadaPagoEscribeSuIngreso:
    def test_el_pago_escribe_un_solo_ingreso_con_su_monto_fecha_temporada_y_autor(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El ingreso del pago
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        encabezados = admin(cliente)
        antes = {m.id for m in movimientos(sesion)}

        pago = pagar_201(cliente, encabezados, abono, cuerpo_pago("30000.00", date(2026, 11, 2)))

        nuevos = [m for m in movimientos(sesion) if m.id not in antes]
        assert len(nuevos) == 1, nuevos
        (mov,) = nuevos
        assert mov.tipo == "ingreso"
        assert mov.origen == "pago"
        assert mov.pago_id == pago["id"]
        es_decimal_exacto(mov.monto, "30000.00")
        assert mov.fecha == date(2026, 11, 2)
        assert mov.temporada_id == p.temporada
        assert mov.registrado_por == p.admin
        assert mov.descripcion is None

    def test_cada_pago_parcial_escribe_su_propio_ingreso(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un ingreso por cada pago parcial
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        encabezados = admin(cliente)
        antes = {m.id for m in movimientos(sesion)}

        primero = pagar_201(cliente, encabezados, abono, cuerpo_pago("30000.00"))
        segundo = pagar_201(cliente, encabezados, abono, cuerpo_pago("55000.00"))

        nuevos = [m for m in movimientos(sesion) if m.id not in antes]
        assert len(nuevos) == 2, nuevos
        assert all(m.tipo == "ingreso" and m.origen == "pago" for m in nuevos), nuevos
        por_pago = {m.pago_id: m.monto for m in nuevos}
        assert por_pago == {
            primero["id"]: Decimal("30000.00"),
            segundo["id"]: Decimal("55000.00"),
        }

    def test_un_pago_rechazado_no_escribe_ningun_movimiento(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago rechazado, sin ingreso
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        encabezados = admin(cliente)
        movimientos_antes = contar_movimientos(sesion)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("55000.01"))

        assert respuesta.status_code == 422, respuesta.text
        assert contar_movimientos(sesion) == movimientos_antes
        assert contar_pagos(sesion) == pagos_antes

    def test_un_pago_sin_permiso_no_escribe_ningun_movimiento(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago sin permiso, sin ingreso
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        crear_usuario(sesion, "lrodriguez", RolUsuario.COORDINADOR)
        encabezados = ingresar(cliente, "lrodriguez")
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 403, respuesta.text
        assert contar_movimientos(sesion) == movimientos_antes
