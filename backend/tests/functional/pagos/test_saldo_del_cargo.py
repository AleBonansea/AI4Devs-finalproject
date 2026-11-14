"""Capability `pagos`: un pago no supera el saldo del cargo (change
cuenta-corriente, tarea 2.1).

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «Un pago no supera el saldo del cargo».

El saldo de un cargo es su total menos sus pagos no anulados. El limite tiene
su caso de adentro («Pago exacto del saldo», 55000.00) y el de afuera («Un
centavo más que el saldo», 55000.01). Con saldo cero, 409 y no 422 (design,
«El servicio de pagos»). «No se guarda nada» se comprueba contando pagos y
movimientos de tesoreria antes y despues.

En «Pago exacto del saldo» la familia tiene ademas otro cargo con un pago: si
el saldo se calculara con los pagos de toda la familia contra el total del
cargo (85000.00 - 35000.00 = 50000.00), 55000.00 se rechazaria.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.pagos.preparacion_api import (
    MENSAJE_SALDADO,
    MENSAJE_SUPERA_SALDO,
    admin,
    contar_movimientos,
    contar_pagos,
    cuerpo_pago,
    insertar_abono_mes,
    insertar_cargo_fijo,
    insertar_pago_previo,
    pagar,
    pagos_del_cargo,
    preparar_perez,
)


class TestUnPagoNoSuperaElSaldoDelCargo:
    def test_un_pago_igual_al_saldo_del_cargo_se_acepta(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago exacto del saldo
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        preinscripcion_ana = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.ana,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
        )
        insertar_pago_previo(sesion, preinscripcion_ana, "5000.00", p.admin)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("55000.00"))

        assert respuesta.status_code == 201, respuesta.text
        assert len(pagos_del_cargo(sesion, abono)) == 2

    def test_un_centavo_mas_que_el_saldo_responde_422_en_monto_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un centavo más que el saldo
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("55000.01"))

        assert respuesta.status_code == 422, respuesta.text
        detalle = respuesta.json()["detail"]
        assert isinstance(detalle, list), detalle
        assert {
            "loc": ["body", "monto"],
            "msg": MENSAJE_SUPERA_SALDO,
            "type": "regla_de_negocio",
        } in [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in detalle]
        assert len(pagos_del_cargo(sesion, abono)) == 1
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_un_cargo_ya_saldado_responde_409_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo saldado
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "50000.00", p.admin)
        insertar_pago_previo(sesion, abono, "35000.00", p.admin)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("0.01"))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SALDADO
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_un_cargo_con_total_cero_responde_409_de_saldado(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo del cien por ciento
        p = preparar_perez(sesion)
        cargo = insertar_abono_mes(sesion, p, base="100000.00", porcentaje="100.00", total="0.00")
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, cargo, cuerpo_pago("100.00"))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SALDADO
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_un_pago_anulado_no_ocupa_saldo_y_se_puede_pagar_el_total(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un pago anulado no ocupa saldo
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "30000.00", p.admin, anulado=True)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("85000.00"))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["saldo_cargo"] == "0.00"
