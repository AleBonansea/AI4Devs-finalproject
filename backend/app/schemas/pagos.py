"""Esquemas de la capability pagos.

La entrada trae el monto como texto, igual que lo devuelve la API, para que un
centavo nunca pase por un `float`. El monto de un pago lo informa el Admin y lo
acota la API (positivo, dos decimales, no más que el saldo); la regla de que el
precio no viene del cliente es sobre el precio de un cargo.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError

_FORMATO_MONTO = re.compile(r"^\d{1,10}(\.\d{1,2})?$")
_CENTAVO = Decimal("0.01")


class PagoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: str
    fecha_pago: date

    @field_validator("monto", mode="before")
    @classmethod
    def _validar_monto(cls, valor: Any) -> str:
        # Antes del tipo: un número JSON no es un `str` y debe dar el mismo error.
        if not isinstance(valor, str) or not _FORMATO_MONTO.fullmatch(valor):
            raise PydanticCustomError(
                "regla_de_negocio", "Tiene que ser un monto con hasta dos decimales."
            )
        monto = Decimal(valor).quantize(_CENTAVO)
        if monto <= 0:
            raise PydanticCustomError("regla_de_negocio", "Tiene que ser mayor que cero.")
        return str(monto)

    @field_validator("fecha_pago")
    @classmethod
    def _no_posterior_a_hoy(cls, valor: date) -> date:
        if valor > date.today():
            raise PydanticCustomError(
                "regla_de_negocio", "La fecha del pago no puede ser posterior a hoy."
            )
        return valor


class PagoRegistrado(BaseModel):
    id: int
    cargo_id: int
    monto: Decimal
    fecha_pago: date
    registrado_por: int
    registrado_en: datetime
    # Lo que falta pagar del cargo, y el saldo de la familia en la temporada.
    saldo_cargo: Decimal
    saldo_pendiente: Decimal
