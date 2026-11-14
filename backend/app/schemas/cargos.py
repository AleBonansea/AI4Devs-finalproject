"""Esquemas de la capability cargos.

La entrada dice QUE se cobra (alumno, tipo, modalidad, período o fecha); no
tiene ningún campo de dinero y rechaza los desconocidos (`extra="forbid"`),
así que un `monto_total` en el cuerpo es un 422 y no se ignora en silencio.
El monto lo calcula y lo guarda la API.

Montos y porcentajes son `Decimal`: Pydantic v2 los serializa como texto, con
la escala que traen (dos decimales), para que un centavo no pase por un float.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import CalculoCargo, CategoriaFamilia, Modalidad


class CargoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: int
    tipo_cargo_id: int
    inscripcion_id: int | None = None
    modalidad: Modalidad | None = None
    periodo_cobro_id: int | None = None
    fecha_dia: date | None = None


class TipoDeCargoOpcion(BaseModel):
    """Un tipo de cargo de la temporada vigente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    calculo: CalculoCargo
    monto_fijo: Decimal | None


class PeriodoOpcion(BaseModel):
    """Un período de cobro (Mes, Quincena o Semana) de la temporada vigente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    modalidad: Modalidad
    nombre: str
    fecha_desde: date
    fecha_hasta: date


class OpcionesDeCargo(BaseModel):
    """Lo que la pantalla necesita para armar un cargo: los tipos y los
    períodos de la temporada vigente."""

    tipos_cargo: list[TipoDeCargoOpcion]
    periodos: list[PeriodoOpcion]


class CargoSimulado(BaseModel):
    """El desglose que el registro guardaría, sin guardar nada."""

    familia_id: int
    categoria_aplicada: CategoriaFamilia
    cantidad_hijos_aplicada: int | None
    monto_base: Decimal
    porcentaje_aplicado: Decimal
    monto_total: Decimal


class CargoRegistrado(CargoSimulado):
    id: int
    temporada_id: int
    alumno_id: int
    tipo_cargo_id: int
    inscripcion_id: int | None
    modalidad: Modalidad | None
    periodo_cobro_id: int | None
    fecha_dia: date | None
    creado_por: int
    creado_en: datetime
    # Se calcula en cada respuesta; no se guarda.
    saldo_pendiente: Decimal
