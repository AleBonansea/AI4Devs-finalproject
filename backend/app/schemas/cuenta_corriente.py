"""Esquemas de salida de la cuenta corriente de una familia.

Montos como `Decimal`: Pydantic v2 los serializa como texto con dos decimales.
Del alumno solo nombre y apellido, para que nada médico se cuele.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import CategoriaFamilia, Modalidad, Turno


class PeriodoDeCargo(BaseModel):
    nombre: str
    fecha_desde: date
    fecha_hasta: date


class PagoEnCuenta(BaseModel):
    """Un pago no anulado: exactamente estos tres campos."""

    id: int
    monto: Decimal
    fecha_pago: date


class CargoEnCuenta(BaseModel):
    """Un cargo de la familia: exactamente estos catorce campos."""

    id: int
    alumno_id: int
    nombre: str
    apellido: str
    tipo_cargo: str
    modalidad: Modalidad | None
    turno: Turno | None
    periodo: PeriodoDeCargo | None
    fecha_dia: date | None
    monto_total: Decimal
    pagado: Decimal
    saldo: Decimal
    creado_en: datetime
    pagos: list[PagoEnCuenta]


class CuentaCorriente(BaseModel):
    familia_id: int
    etiqueta: str
    categoria: CategoriaFamilia
    total_cargos: Decimal
    total_pagado: Decimal
    saldo_pendiente: Decimal
    cargos: list[CargoEnCuenta]
