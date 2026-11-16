"""Preparacion compartida de los tests de esquema de `pago` y de
`tesoreria_movimiento`.

No es un archivo de tests (pytest no lo junta: no empieza con `test_`). Lo
usan `pagos/test_esquema_pago.py` y `tesoreria/test_esquema_movimiento.py`.

Temporada, usuario, familia y alumno salen de `asistencia/preparacion.py`;
el tipo de cargo, de `cargos/preparacion.py`. El cargo que cuelga los pagos
es una «Preinscripción» de monto fijo insertada con SQL crudo, coherente con
los `CHECK` de `cargo`: sin inscripcion, modalidad, periodo, fecha ni
cantidad de hijos, porcentaje 0 y total = base.

Los pagos y los movimientos se insertan con SQL crudo sobre las columnas de
`3-modelo-de-datos.md` («`pago`» y «`tesoreria_movimiento`»). `creado_en` y
`registrado_en` no se escriben: tienen valor por defecto en la base.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    crear_alumno,
    crear_familia,
    crear_usuario,
    crear_vigente,
)
from tests.functional.cargos.preparacion import tipo_cargo


@dataclass(frozen=True)
class ConCargo:
    """La temporada 2026-27, el Admin `mgarcia` y una «Preinscripción» de
    20000.00 de Juan Pérez, sin pagos."""

    temporada: int
    admin: int
    cargo: int


def preparar_cargo(sesion: Session) -> ConCargo:
    temporada = crear_vigente(sesion)
    admin = crear_usuario(sesion, "mgarcia", RolUsuario.ADMIN)
    familia = crear_familia(sesion, "empleado")
    juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia, nacimiento=date(2020, 3, 10))
    preinscripcion = tipo_cargo(sesion, temporada, "Preinscripción", "monto_fijo", "20000.00")
    cargo = int(
        sesion.execute(
            text(
                "INSERT INTO cargo ("
                "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
                "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
                "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
                ") VALUES ("
                ":t, :f, :a, :tc, NULL, NULL, NULL, NULL, 'empleado', NULL, "
                ":m, 0, :m, :u, now()) RETURNING id"
            ),
            {
                "t": temporada,
                "f": familia,
                "a": juan,
                "tc": preinscripcion,
                "m": Decimal("20000.00"),
                "u": admin,
            },
        ).scalar_one()
    )
    return ConCargo(temporada=temporada, admin=admin, cargo=cargo)


# --- pago ----------------------------------------------------------------------

INSERTAR_PAGO = (
    "INSERT INTO pago ("
    "cargo_id, monto, fecha_pago, registrado_por, anulado_en, anulado_por, motivo_anulacion"
    ") VALUES ("
    ":cargo_id, :monto, :fecha_pago, :registrado_por, :anulado_en, :anulado_por, "
    ":motivo_anulacion"
    ") RETURNING id"
)


def fila_pago(c: ConCargo, **cambios: object) -> dict[str, object]:
    """Un pago valido de 30000.00 del 2026-11-02, sin anulacion. `cambios`
    pisa las columnas que el test necesita distintas."""
    fila: dict[str, object] = {
        "cargo_id": c.cargo,
        "monto": Decimal("30000.00"),
        "fecha_pago": date(2026, 11, 2),
        "registrado_por": c.admin,
        "anulado_en": None,
        "anulado_por": None,
        "motivo_anulacion": None,
    }
    fila.update(cambios)
    return fila


def insertar_pago(sesion: Session, fila: Mapping[str, object]) -> int:
    return int(sesion.execute(text(INSERTAR_PAGO), fila).scalar_one())


def contar(sesion: Session, tabla: str) -> int:
    # `tabla` es siempre un literal de los tests, nunca un dato de afuera.
    return int(sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one())


# --- comprobaciones --------------------------------------------------------------


def rechaza(sesion: Session, sql: str, fila: Mapping[str, object], *restricciones: str) -> None:
    """La fila tiene que fallar en la base, aislada en un savepoint, por una
    de `restricciones`."""
    with pytest.raises(IntegrityError) as error, sesion.begin_nested():
        sesion.execute(text(sql), fila)
    assert error.value.orig is not None
    nombre = error.value.orig.diag.constraint_name  # type: ignore[union-attr]
    assert nombre in restricciones, f"Salto {nombre!r}, se esperaba {restricciones}"


def es_decimal_exacto(valor: object, esperado: str) -> None:
    assert isinstance(valor, Decimal), f"Se leyo {type(valor).__name__}, no Decimal"
    assert valor == Decimal(esperado)
    assert valor.as_tuple().exponent == -2, f"{valor} no quedo con dos decimales"
