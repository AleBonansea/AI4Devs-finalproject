"""Capability `pagos`: el cargo del pago existe y es de una temporada abierta
(change cuenta-corriente, tarea 2.1).

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «El cargo del pago existe y es de una temporada abierta».

Los 404 traen `detail` de texto; el id fuera de `bigint` tambien es 404 y no
500. El 409 de la temporada cerrada no guarda ni pago ni movimiento.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_cerrada
from tests.functional.pagos.preparacion_api import (
    ID_FUERA_DE_RANGO,
    ID_INEXISTENTE,
    MENSAJE_CARGO_INEXISTENTE,
    MENSAJE_TEMPORADA_CERRADA,
    admin,
    contar_movimientos,
    contar_pagos,
    cuerpo_pago,
    insertar_abono_mes,
    insertar_cargo_fijo,
    nuevo_tipo_fijo,
    pagar,
    preparar_perez,
)


class TestElCargoDelPagoExisteYEsDeUnaTemporadaAbierta:
    def test_un_cargo_que_no_existe_responde_404(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo que no existe
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        assert abono != ID_INEXISTENTE
        pagos_antes = contar_pagos(sesion)

        respuesta = pagar(cliente, admin(cliente), ID_INEXISTENTE, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_CARGO_INEXISTENTE
        assert contar_pagos(sesion) == pagos_antes

    def test_un_id_mas_grande_que_el_maximo_responde_404(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Id de cargo más grande que el máximo
        preparar_perez(sesion)

        respuesta = pagar(cliente, admin(cliente), ID_FUERA_DE_RANGO, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_CARGO_INEXISTENTE

    def test_un_cargo_de_una_temporada_cerrada_responde_409_y_no_guarda_nada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo de una temporada cerrada
        p = preparar_perez(sesion)
        cerrada = crear_cerrada(sesion)
        cargo_viejo = insertar_cargo_fijo(
            sesion,
            temporada=cerrada,
            familia=p.familia,
            alumno=p.juan,
            tipo=nuevo_tipo_fijo(sesion, cerrada, "Preinscripción", "30000.00"),
            monto="30000.00",
            creado_por=p.admin,
        )
        encabezados = admin(cliente)
        pagos_antes = contar_pagos(sesion)
        movimientos_antes = contar_movimientos(sesion)

        respuesta = pagar(cliente, encabezados, cargo_viejo, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_TEMPORADA_CERRADA
        assert contar_pagos(sesion) == pagos_antes
        assert contar_movimientos(sesion) == movimientos_antes
