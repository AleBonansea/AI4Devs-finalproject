"""Cálculo de un cargo: función pura.

Este es el único lugar donde se calcula un precio. Ningún endpoint, modelo ni
componente recalcula un monto por su cuenta. La función no toca la base, no
lee el request y no tiene efectos: recibe la tarifa base, la categoría, la
modalidad, la cantidad de hijos y la tabla de descuentos ya cargada, y
devuelve el desglose que el cargo guarda para no recalcularse nunca.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import CategoriaFamilia, Modalidad

_CENTAVO = Decimal("0.01")
_CIEN = Decimal(100)

# Del cuarto hijo en adelante rige el mismo porcentaje: la tabla del Mes tiene
# tramos 1, 2, 3 y «4 o más», guardado como tramo 4.
_TRAMO_MAXIMO = 4


@dataclass(frozen=True)
class TablaDescuentos:
    """Descuentos de una temporada, en porcentaje (50 es 50 %).

    `por_modalidad` cubre Día, Semana y Quincena (la cantidad de hijos no
    interviene); `mes` cubre el Mes por categoría y tramo de hijos.
    """

    por_modalidad: dict[tuple[CategoriaFamilia, Modalidad], Decimal]
    mes: dict[tuple[CategoriaFamilia, int], Decimal]


@dataclass(frozen=True)
class Desglose:
    """Lo que se guarda en el cargo: el cálculo congelado."""

    categoria_aplicada: CategoriaFamilia
    cantidad_hijos_aplicada: int | None
    monto_base: Decimal
    porcentaje_aplicado: Decimal
    monto_total: Decimal


class FaltaDescuento(Exception):  # noqa: N818 - el nombre lo fija el diseño del change
    """La tabla de descuentos no tiene la celda que el cálculo necesita."""

    def __init__(
        self,
        categoria: CategoriaFamilia,
        modalidad: Modalidad,
        tramo: int | None,
    ) -> None:
        self.categoria = categoria
        self.modalidad = modalidad
        self.tramo = tramo
        detalle = f"categoría {categoria.value}, modalidad {modalidad.value}"
        if tramo is not None:
            detalle += f", tramo de {tramo} hijo(s)"
        super().__init__(f"Falta el descuento configurado para {detalle}.")


def _dos_decimales(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTAVO, rounding=ROUND_HALF_UP)


def calcular_abono(
    *,
    tarifa_base: Decimal,
    categoria: CategoriaFamilia,
    modalidad: Modalidad,
    cantidad_hijos: int | None,
    descuentos: TablaDescuentos,
) -> Desglose:
    """Calcula un abono aplicando un único porcentaje a la tarifa base.

    En el Mes el porcentaje sale de la categoría y del tramo de hijos
    (`min(cantidad_hijos, 4)`, porque «4 o más» es una sola fila); se guarda la
    cantidad contada y no el tramo. En las demás modalidades la cantidad de
    hijos no interviene y se devuelve `None`.

    El redondeo es half-up a dos decimales, igual que `round()` de Postgres
    sobre numéricos: tiene que coincidir con el CHECK `ck_cargo_total` de la
    tabla `cargo`, o la base rechazaría el cargo.
    """
    if modalidad is Modalidad.MES:
        if cantidad_hijos is None or cantidad_hijos < 1:
            raise ValueError("El Mes necesita una cantidad de hijos de al menos 1.")
        tramo = min(cantidad_hijos, _TRAMO_MAXIMO)
        porcentaje = descuentos.mes.get((categoria, tramo))
        if porcentaje is None:
            raise FaltaDescuento(categoria, modalidad, tramo)
        hijos_aplicados: int | None = cantidad_hijos
    else:
        porcentaje = descuentos.por_modalidad.get((categoria, modalidad))
        if porcentaje is None:
            raise FaltaDescuento(categoria, modalidad, None)
        hijos_aplicados = None

    total = _dos_decimales(tarifa_base * (_CIEN - porcentaje) / _CIEN)
    return Desglose(
        categoria_aplicada=categoria,
        cantidad_hijos_aplicada=hijos_aplicados,
        monto_base=_dos_decimales(tarifa_base),
        porcentaje_aplicado=_dos_decimales(porcentaje),
        monto_total=total,
    )


def calcular_monto_fijo(*, monto_fijo: Decimal, categoria: CategoriaFamilia) -> Desglose:
    """Cargo de monto fijo: sin descuento, el total es el monto configurado."""
    monto = _dos_decimales(monto_fijo)
    return Desglose(
        categoria_aplicada=categoria,
        cantidad_hijos_aplicada=None,
        monto_base=monto,
        porcentaje_aplicado=Decimal("0.00"),
        monto_total=monto,
    )
