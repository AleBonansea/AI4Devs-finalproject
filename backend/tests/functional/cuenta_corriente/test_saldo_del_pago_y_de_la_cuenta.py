"""Capability `pagos`: el saldo del cargo coincide con la cuenta corriente
(change cuenta-corriente, tarea 3.1).

Scenario «El saldo del cargo coincide con la cuenta corriente», del
Requirement «Registrar un pago», en
`openspec/changes/cuenta-corriente/specs/pagos/spec.md`. Los otros Scenarios
de ese Requirement estan en `pagos/test_registrar_pago.py`.

El pago se registra por la API (`POST /api/v1/cargos/{cargo_id}/pagos`) y
enseguida se pide `GET /api/v1/familias/{familia_id}/cuenta-corriente`.

85000.00 - 30000.00 - 12345.50 - 10000.25 = 32654.25. Perder uno de los
pagos previos o los centavos da otro numero: 62654.25 sin el de 30000.00,
44999.75 sin el de 12345.50, 42654.50 sin el nuevo, 32654.00 sin centavos.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.cuenta_corriente.preparacion import cargo_de, pedir_200
from tests.functional.pagos.preparacion_api import (
    admin,
    cuerpo_pago,
    insertar_abono_mes,
    insertar_pago_previo,
    pagar_201,
    preparar_perez,
)


class TestRegistrarUnPagoYVerLaCuenta:
    def test_el_saldo_del_cargo_del_pago_es_el_mismo_que_el_de_la_cuenta_corriente(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El saldo del cargo coincide con la cuenta corriente
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # 85000.00, vigente
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        insertar_pago_previo(sesion, abono, "12345.50", p.admin)
        encabezados = admin(cliente)

        pago = pagar_201(cliente, encabezados, abono, cuerpo_pago("10000.25"))
        cuenta = pedir_200(cliente, encabezados, p.familia)

        assert pago["saldo_cargo"] == "32654.25"
        assert cargo_de(cuenta, abono)["saldo"] == "32654.25"
        assert cargo_de(cuenta, abono)["saldo"] == pago["saldo_cargo"]
