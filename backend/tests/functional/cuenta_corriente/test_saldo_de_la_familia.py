"""Capability `cuenta-corriente`: el saldo de la familia es cargos menos pagos
(change cuenta-corriente, tarea 3.1).

Un test por Scenario del Requirement «El saldo de la familia es cargos menos
pagos», en `openspec/changes/cuenta-corriente/specs/cuenta-corriente/spec.md`.

Endpoint: `GET /api/v1/familias/{familia_id}/cuenta-corriente`, solo Admin.
Montos como texto exacto con dos decimales.

Datos elegidos para que un error plausible de otro numero:
- «Dos cargos con pagos parciales»: el Abono tiene DOS pagos. Un `JOIN`
  directo de cargo con pago repite su total por cada pago: `total_cargos`
  daria 190000.00 en vez de 105000.00. Olvidar los pagos de uno de los dos
  cargos da `total_pagado` 40000.00 o 5000.00.
- «Un pago anulado no cuenta»: contar el anulado da `total_pagado` 50000.00
  y `saldo_pendiente` 35000.00.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.cuenta_corriente.preparacion import cargo_de, pedir_200
from tests.functional.pagos.preparacion_api import (
    admin,
    insertar_abono_mes,
    insertar_cargo_fijo,
    insertar_pago_previo,
    preparar_perez,
)


class TestElSaldoDeLaFamiliaEsCargosMenosPagos:
    def test_los_totales_y_el_saldo_de_cada_cargo_cuentan_cada_pago_una_vez(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Dos cargos con pagos parciales
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # 85000.00
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        insertar_pago_previo(sesion, abono, "10000.00", p.admin)
        preinscripcion = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.ana,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
        )
        insertar_pago_previo(sesion, preinscripcion, "5000.00", p.admin)

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert cuerpo["total_cargos"] == "105000.00"
        assert cuerpo["total_pagado"] == "45000.00"
        assert cuerpo["saldo_pendiente"] == "60000.00"
        del_abono = cargo_de(cuerpo, abono)
        assert del_abono["pagado"] == "40000.00"
        assert del_abono["saldo"] == "45000.00"
        de_la_preinscripcion = cargo_de(cuerpo, preinscripcion)
        assert de_la_preinscripcion["pagado"] == "5000.00"
        assert de_la_preinscripcion["saldo"] == "15000.00"

    def test_un_pago_anulado_no_cuenta_en_el_saldo_ni_se_lista(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un pago anulado no cuenta
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # 85000.00
        vigente = insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        insertar_pago_previo(sesion, abono, "20000.00", p.admin, anulado=True)

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert cuerpo["total_pagado"] == "30000.00"
        assert cuerpo["saldo_pendiente"] == "55000.00"
        cargo = cargo_de(cuerpo, abono)
        assert [(pago["id"], pago["monto"]) for pago in cargo["pagos"]] == [(vigente, "30000.00")]
        # El saldo del cargo sigue la misma regla que el de la familia.
        assert cargo["saldo"] == "55000.00"

    def test_un_cargo_del_cien_por_ciento_deja_saldo_cero(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo del cien por ciento
        p = preparar_perez(sesion)
        cargo = insertar_abono_mes(sesion, p, base="100000.00", porcentaje="100.00", total="0.00")

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert len(cuerpo["cargos"]) == 1
        assert cargo_de(cuerpo, cargo)["saldo"] == "0.00"
        assert cuerpo["saldo_pendiente"] == "0.00"
