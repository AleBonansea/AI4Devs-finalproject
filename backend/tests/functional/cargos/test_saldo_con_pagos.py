"""Capability `cargos`: el saldo pendiente al registrar descuenta los pagos.

Scenario «La familia ya pagó una parte» del Requirement modificado «Saldo
pendiente al registrar», en `openspec/changes/cuenta-corriente/specs/cargos/spec.md`.
Los otros dos Scenarios de ese Requirement estan en `test_registrar.py`.

La Preinscripcion de Ana y sus pagos se insertan directo en la base (el
anulado con sus tres datos de anulacion): no son lo que se prueba. El Abono
del Mes de Juan se registra por la API: 100000.00 al 15 % (empleado, 2 hijos
en el turno) = 85000.00.

Saldo esperado: 20000.00 + 85000.00 - 5000.00 = 100000.00. Si se ignoraran
los pagos daria 105000.00; si se contara el anulado, 97000.00.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    Hijo,
    Vigente,
    abono_mes,
    admin,
    descuentos_mes,
    familia_con_hijos,
    preparar_vigente,
    tarifa,
)
from tests.functional.pagos.preparacion_api import insertar_cargo_fijo, insertar_pago_previo


def _preparar_perez_con_pagos(sesion: Session) -> tuple[Vigente, Hijo]:
    """La familia «Pérez – Ana» (empleado, Ana y Juan en el turno manana) con
    la Preinscripcion de Ana por 20000.00, un pago de 5000.00 y otro de
    3000.00 anulado. Devuelve la vigente y a Juan."""
    v = preparar_vigente(sesion)
    tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
    descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
    familia, (ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
    preinscripcion_ana = insertar_cargo_fijo(
        sesion,
        temporada=v.temporada,
        familia=familia,
        alumno=ana.alumno,
        tipo=v.preinscripcion,
        monto="20000.00",
        creado_por=v.admin,
    )
    insertar_pago_previo(sesion, preinscripcion_ana, "5000.00", v.admin)
    insertar_pago_previo(sesion, preinscripcion_ana, "3000.00", v.admin, anulado=True)
    return v, juan


class TestSaldoPendienteAlRegistrarConPagos:
    def test_el_saldo_descuenta_el_pago_vigente_y_no_el_anulado(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: La familia ya pagó una parte
        v, juan = _preparar_perez_con_pagos(sesion)
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["monto_total"] == "85000.00"
        assert cuerpo["saldo_pendiente"] == "100000.00"
