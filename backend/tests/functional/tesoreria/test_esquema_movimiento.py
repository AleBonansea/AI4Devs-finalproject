"""Capability `tesoreria`: las restricciones de la tabla `tesoreria_movimiento`.

Un test por Scenario de
`openspec/changes/cuenta-corriente/specs/tesoreria/spec.md`, Requirements
«La forma de un movimiento de tesorería» y «Un pago tiene un solo movimiento
de cada origen».

No hay endpoints de tesoreria, asi que el contrato que se prueba es el de la
base: cada test inserta con SQL crudo sobre las columnas de
`3-modelo-de-datos.md` («`tesoreria_movimiento`») y comprueba que Postgres
guarde o rechace la fila. Los nombres de las restricciones son los de
`openspec/changes/cuenta-corriente/design.md`, seccion «Esquema: `pago`,
`tesoreria_movimiento` y dos enumerados».

`creado_en` no se escribe: tiene valor por defecto. Tampoco `cierre_canon_id`,
que segun el design llega con `cierre_canon`.

Cada fila de un test de rechazo es valida en todo lo demas. Cada sentencia
rechazada va dentro de `sesion.begin_nested()`. Montos como `Decimal` exacto.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.pagos.preparacion import (
    contar,
    es_decimal_exacto,
    fila_pago,
    insertar_pago,
    preparar_cargo,
    rechaza,
)

INSERTAR_MOVIMIENTO = (
    "INSERT INTO tesoreria_movimiento ("
    "temporada_id, tipo, origen, pago_id, descripcion, monto, fecha, registrado_por"
    ") VALUES ("
    ":temporada_id, CAST(:tipo AS tipo_movimiento), CAST(:origen AS origen_movimiento), "
    ":pago_id, :descripcion, :monto, :fecha, :registrado_por"
    ") RETURNING id"
)


@dataclass(frozen=True)
class ConPago:
    """La temporada 2026-27, el Admin `mgarcia` y un pago de 30000.00 del
    2026-11-02 sobre una «Preinscripción» de Juan, sin movimientos."""

    temporada: int
    admin: int
    pago: int


@pytest.fixture
def p(sesion: Session) -> ConPago:
    c = preparar_cargo(sesion)
    return ConPago(temporada=c.temporada, admin=c.admin, pago=insertar_pago(sesion, fila_pago(c)))


def _ingreso_del_pago(p: ConPago, **cambios: object) -> dict[str, object]:
    """El ingreso valido del pago: `ingreso`, origen `pago`, 30000.00."""
    fila: dict[str, object] = {
        "temporada_id": p.temporada,
        "tipo": "ingreso",
        "origen": "pago",
        "pago_id": p.pago,
        "descripcion": None,
        "monto": Decimal("30000.00"),
        "fecha": date(2026, 11, 2),
        "registrado_por": p.admin,
    }
    fila.update(cambios)
    return fila


def _egreso_manual(p: ConPago, **cambios: object) -> dict[str, object]:
    """Un egreso manual valido: con descripcion y sin pago."""
    base: dict[str, object] = {
        "tipo": "egreso",
        "origen": "manual",
        "pago_id": None,
        "descripcion": "Insumos de librería",
        "monto": Decimal("12500.00"),
        "fecha": date(2026, 11, 3),
    }
    base.update(cambios)
    return _ingreso_del_pago(p, **base)


def _insertar(sesion: Session, fila: dict[str, object]) -> int:
    return int(sesion.execute(text(INSERTAR_MOVIMIENTO), fila).scalar_one())


def _movimientos(sesion: Session) -> int:
    return contar(sesion, "tesoreria_movimiento")


# --- Requirement: La forma de un movimiento de tesoreria ------------------------


class TestLaFormaDeUnMovimiento:
    def test_un_ingreso_de_origen_pago_con_su_pago_queda_guardado(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Ingreso por un pago
        movimiento = _insertar(sesion, _ingreso_del_pago(p))

        fila = sesion.execute(
            text(
                "SELECT temporada_id, tipo::text AS tipo, origen::text AS origen, pago_id, "
                "descripcion, monto, fecha, registrado_por, creado_en "
                "FROM tesoreria_movimiento WHERE id = :id"
            ),
            {"id": movimiento},
        ).one()
        assert fila.temporada_id == p.temporada
        assert fila.tipo == "ingreso"
        assert fila.origen == "pago"
        assert fila.pago_id == p.pago
        assert fila.descripcion is None
        es_decimal_exacto(fila.monto, "30000.00")
        assert fila.fecha == date(2026, 11, 2)
        assert fila.registrado_por == p.admin
        assert fila.creado_en is not None

    def test_la_base_rechaza_un_movimiento_de_origen_pago_registrado_como_egreso(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Pago registrado como egreso
        rechaza(
            sesion,
            INSERTAR_MOVIMIENTO,
            _ingreso_del_pago(p, tipo="egreso"),
            "ck_movimiento_origen",
        )

        assert _movimientos(sesion) == 0

    def test_la_base_rechaza_un_ingreso_de_origen_pago_sin_pago(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Origen pago sin pago
        rechaza(
            sesion,
            INSERTAR_MOVIMIENTO,
            _ingreso_del_pago(p, pago_id=None),
            "ck_movimiento_origen",
        )

        assert _movimientos(sesion) == 0

    def test_un_egreso_manual_con_descripcion_y_sin_pago_queda_guardado(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Egreso manual con descripcion
        movimiento = _insertar(sesion, _egreso_manual(p))

        fila = sesion.execute(
            text(
                "SELECT tipo::text AS tipo, origen::text AS origen, pago_id, descripcion, monto "
                "FROM tesoreria_movimiento WHERE id = :id"
            ),
            {"id": movimiento},
        ).one()
        assert fila.tipo == "egreso"
        assert fila.origen == "manual"
        assert fila.pago_id is None
        assert fila.descripcion == "Insumos de librería"
        es_decimal_exacto(fila.monto, "12500.00")

    def test_la_base_rechaza_un_egreso_manual_sin_descripcion(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Egreso manual sin descripcion
        rechaza(
            sesion,
            INSERTAR_MOVIMIENTO,
            _egreso_manual(p, descripcion=None),
            "ck_movimiento_origen",
        )

        assert _movimientos(sesion) == 0

    def test_la_base_rechaza_un_movimiento_del_canon_mientras_no_hay_cierre_de_canon(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Movimiento del canon. Fila en todo lo demas como la de un
        # egreso del canon: `egreso`, con descripcion y sin pago.
        rechaza(
            sesion,
            INSERTAR_MOVIMIENTO,
            _egreso_manual(p, origen="canon", descripcion="Canon de enero"),
            "ck_movimiento_origen",
        )

        assert _movimientos(sesion) == 0

    def test_la_base_rechaza_un_ingreso_del_pago_con_monto_cero(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Monto en cero. El caso de adentro (un monto positivo) es
        # «Ingreso por un pago».
        rechaza(
            sesion,
            INSERTAR_MOVIMIENTO,
            _ingreso_del_pago(p, monto=Decimal("0.00")),
            "ck_movimiento_monto_positivo",
        )

        assert _movimientos(sesion) == 0


# --- Requirement: Un pago tiene un solo movimiento de cada origen ---------------


class TestUnPagoTieneUnSoloMovimientoDeCadaOrigen:
    def test_la_base_rechaza_un_segundo_ingreso_del_mismo_pago(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Segundo ingreso del mismo pago
        _insertar(sesion, _ingreso_del_pago(p))

        rechaza(sesion, INSERTAR_MOVIMIENTO, _ingreso_del_pago(p), "uq_movimiento_pago_origen")

        assert _movimientos(sesion) == 1

    def test_el_egreso_de_anulacion_del_mismo_pago_queda_guardado(
        self, sesion: Session, p: ConPago
    ) -> None:
        # Scenario: Egreso de anulacion del mismo pago
        _insertar(sesion, _ingreso_del_pago(p))

        _insertar(
            sesion,
            _ingreso_del_pago(p, tipo="egreso", origen="anulacion_pago", fecha=date(2026, 11, 5)),
        )

        filas = sesion.execute(
            text(
                "SELECT tipo::text AS tipo, origen::text AS origen, monto "
                "FROM tesoreria_movimiento WHERE pago_id = :p ORDER BY origen::text"
            ),
            {"p": p.pago},
        ).all()
        assert [(f.tipo, f.origen) for f in filas] == [
            ("egreso", "anulacion_pago"),
            ("ingreso", "pago"),
        ]
        for f in filas:
            es_decimal_exacto(f.monto, "30000.00")
