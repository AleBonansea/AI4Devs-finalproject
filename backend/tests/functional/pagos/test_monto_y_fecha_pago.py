"""Capability `pagos`: el monto y la fecha del pago (change cuenta-corriente,
tarea 2.1).

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «El monto y la fecha del pago».

Cada pedido va sobre un cargo existente de 85000.00 sin pagos, de la temporada
vigente, y es valido en todo lo demas: el rechazo tiene que salir del campo
que se prueba y no de un 404 o de otro campo.

La fecha se compara con la de HOY del servidor: los Scenarios de hoy y de
manana usan `date.today()`, no una fecha fija. 2026-11-10 es anterior a hoy.

Limites con su caso de adentro dentro del mismo test, como contraste:
- diez cifras enteras pasan el formato (y chocan con el saldo), once no;
- 0.01 se acepta, 0.00 no.
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.pagos.preparacion_api import (
    FECHA_PAGO,
    MENSAJE_FECHA_FUTURA,
    MENSAJE_FORMATO_MONTO,
    MENSAJE_MAYOR_QUE_CERO,
    MENSAJE_OBLIGATORIO,
    MENSAJE_SUPERA_SALDO,
    Perez,
    admin,
    contar_movimientos,
    contar_pagos,
    cuerpo_pago,
    exigir_error_en,
    insertar_abono_mes,
    pagar,
    preparar_perez,
)


def _abono(sesion: Session) -> tuple[Perez, int]:
    p = preparar_perez(sesion)
    return p, insertar_abono_mes(sesion, p)


class TestElMontoYLaFechaDelPago:
    def test_un_monto_con_tres_decimales_responde_422_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto con tres decimales
        _, abono = _abono(sesion)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("4462.505"))

        exigir_error_en(respuesta, "monto", MENSAJE_FORMATO_MONTO)
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_un_monto_como_numero_json_responde_422(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto como número
        _, abono = _abono(sesion)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago(4462.50))

        exigir_error_en(respuesta, "monto", MENSAJE_FORMATO_MONTO)
        assert contar_pagos(sesion) == pagos_antes

    def test_un_monto_escrito_con_coma_responde_422(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto escrito con coma
        _, abono = _abono(sesion)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("4462,50"))

        exigir_error_en(respuesta, "monto", MENSAJE_FORMATO_MONTO)
        assert contar_pagos(sesion) == pagos_antes

    def test_un_monto_en_cero_responde_422_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto en cero
        _, abono = _abono(sesion)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("0.00"))

        exigir_error_en(respuesta, "monto", MENSAJE_MAYOR_QUE_CERO)
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

        # Contraste, el caso de adentro: un centavo si se acepta.
        un_centavo = pagar(cliente, encabezados, abono, cuerpo_pago("0.01"))
        assert un_centavo.status_code == 201, un_centavo.text

    def test_un_monto_con_once_cifras_enteras_responde_422_de_formato(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto con once cifras enteras
        _, abono = _abono(sesion)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("12345678901.00"))

        exigir_error_en(respuesta, "monto", MENSAJE_FORMATO_MONTO)
        assert contar_pagos(sesion) == pagos_antes

        # Contraste, el caso de adentro: diez cifras enteras pasan el formato
        # y lo que las rechaza es el saldo del cargo, no el formato.
        diez_cifras = pagar(cliente, encabezados, abono, cuerpo_pago("1234567890.00"))
        errores = exigir_error_en(diez_cifras, "monto", MENSAJE_SUPERA_SALDO)
        assert MENSAJE_FORMATO_MONTO not in [e["msg"] for e in errores]
        assert contar_pagos(sesion) == pagos_antes

    def test_un_pago_con_la_fecha_de_hoy_se_acepta(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago con fecha de hoy
        _, abono = _abono(sesion)
        hoy = date.today()

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("10000.00", hoy))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["fecha_pago"] == hoy.isoformat()

    def test_un_pago_con_la_fecha_de_manana_responde_422_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago con fecha de mañana
        _, abono = _abono(sesion)
        encabezados = admin(cliente)
        manana = date.today() + timedelta(days=1)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, abono, cuerpo_pago("10000.00", manana))

        exigir_error_en(respuesta, "fecha_pago", MENSAJE_FECHA_FUTURA)
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes

    def test_un_pago_anterior_al_inicio_de_la_temporada_se_acepta(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago anterior al inicio de la temporada
        # La temporada vigente empieza el 2027-01-04 (asistencia/preparacion.py).
        _, abono = _abono(sesion)
        fecha = date(2026, 11, 10)
        assert fecha < date.today()

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("20000.00", fecha))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["fecha_pago"] == "2026-11-10"

    def test_un_pago_sin_fecha_responde_422_con_dato_obligatorio(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Sin fecha
        _, abono = _abono(sesion)
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, admin(cliente), abono, {"monto": "10000.00"})

        exigir_error_en(respuesta, "fecha_pago", MENSAJE_OBLIGATORIO)
        assert contar_pagos(sesion) == pagos_antes

    def test_un_campo_desconocido_en_el_cuerpo_responde_422_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Campo desconocido en el cuerpo
        _, abono = _abono(sesion)
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)
        cuerpo = {**cuerpo_pago("10000.00", FECHA_PAGO), "medio": "efectivo"}

        respuesta = pagar(cliente, encabezados, abono, cuerpo)

        assert respuesta.status_code == 422, respuesta.text
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes
