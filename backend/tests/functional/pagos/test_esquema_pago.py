"""Capability `pagos`: las restricciones de la tabla `pago`.

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «El pago guarda su monto, su fecha y su autor».

El endpoint todavia no existe, asi que el contrato que se prueba es el de la
base: cada test inserta con SQL crudo sobre las columnas de
`3-modelo-de-datos.md` («`pago`») y comprueba que Postgres guarde o rechace
la fila. Los nombres de las restricciones son los de
`openspec/changes/cuenta-corriente/design.md`, seccion «Esquema: `pago`,
`tesoreria_movimiento` y dos enumerados»: mirar cual salto asegura que la
fila se rechazo por la regla del Scenario y no por otra cosa.

Cada fila de un test de rechazo es valida en todo lo demas. Cada sentencia
rechazada va dentro de `sesion.begin_nested()`. Montos como `Decimal` exacto.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.pagos.preparacion import (
    INSERTAR_PAGO,
    ConCargo,
    contar,
    es_decimal_exacto,
    fila_pago,
    insertar_pago,
    preparar_cargo,
    rechaza,
)

ANULADO_EN = datetime(2026, 11, 5, 13, 0, tzinfo=UTC)


@pytest.fixture
def c(sesion: Session) -> ConCargo:
    return preparar_cargo(sesion)


class TestElPagoGuardaSuMontoSuFechaYSuAutor:
    def test_un_pago_valido_de_un_cargo_existente_queda_guardado(
        self, sesion: Session, c: ConCargo
    ) -> None:
        # Scenario: Pago valido
        pago_id = insertar_pago(sesion, fila_pago(c))

        fila = sesion.execute(
            text(
                "SELECT cargo_id, monto, fecha_pago, registrado_por, registrado_en, "
                "anulado_en, anulado_por, motivo_anulacion FROM pago WHERE id = :id"
            ),
            {"id": pago_id},
        ).one()
        assert fila.cargo_id == c.cargo
        es_decimal_exacto(fila.monto, "30000.00")
        assert fila.fecha_pago == date(2026, 11, 2)
        assert fila.registrado_por == c.admin
        # `registrado_en` no se escribio: lo pone el default de la base.
        assert fila.registrado_en is not None
        assert fila.anulado_en is None
        assert fila.anulado_por is None
        assert fila.motivo_anulacion is None

    def test_la_base_rechaza_un_pago_con_monto_cero(self, sesion: Session, c: ConCargo) -> None:
        # Scenario: Monto en cero. El caso de adentro es «Monto de un centavo».
        rechaza(
            sesion, INSERTAR_PAGO, fila_pago(c, monto=Decimal("0.00")), "ck_pago_monto_positivo"
        )

        assert contar(sesion, "pago") == 0

    def test_un_pago_de_un_centavo_queda_guardado(self, sesion: Session, c: ConCargo) -> None:
        # Scenario: Monto de un centavo
        pago_id = insertar_pago(sesion, fila_pago(c, monto=Decimal("0.01")))

        monto = sesion.execute(
            text("SELECT monto FROM pago WHERE id = :id"), {"id": pago_id}
        ).scalar_one()
        es_decimal_exacto(monto, "0.01")

    def test_la_base_rechaza_un_pago_de_un_cargo_que_no_existe(
        self, sesion: Session, c: ConCargo
    ) -> None:
        # Scenario: Cargo que no existe
        inexistente = int(
            sesion.execute(text("SELECT coalesce(max(id), 0) + 1000 FROM cargo")).scalar_one()
        )

        rechaza(sesion, INSERTAR_PAGO, fila_pago(c, cargo_id=inexistente), "fk_pago_cargo")

        assert contar(sesion, "pago") == 0

    def test_la_base_rechaza_una_anulacion_sin_motivo(self, sesion: Session, c: ConCargo) -> None:
        # Scenario: Anulacion a medias
        rechaza(
            sesion,
            INSERTAR_PAGO,
            fila_pago(c, anulado_en=ANULADO_EN, anulado_por=c.admin, motivo_anulacion=None),
            "ck_pago_anulacion_completa",
        )

        assert contar(sesion, "pago") == 0

    def test_un_pago_con_los_tres_datos_de_anulacion_queda_guardado(
        self, sesion: Session, c: ConCargo
    ) -> None:
        # Scenario: Anulacion completa
        pago_id = insertar_pago(
            sesion,
            fila_pago(
                c,
                anulado_en=ANULADO_EN,
                anulado_por=c.admin,
                motivo_anulacion="Cobro cargado dos veces",
            ),
        )

        fila = sesion.execute(
            text("SELECT anulado_en, anulado_por, motivo_anulacion FROM pago WHERE id = :id"),
            {"id": pago_id},
        ).one()
        assert fila.anulado_en == ANULADO_EN
        assert fila.anulado_por == c.admin
        assert fila.motivo_anulacion == "Cobro cargado dos veces"
