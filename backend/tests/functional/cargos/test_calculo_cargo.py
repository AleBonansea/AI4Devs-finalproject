"""Capability `cargos`: la funcion pura del calculo de un cargo.

Excepcion a «se prueba por la API»: `openspec/changes/cobro/design.md`,
seccion «El calculo, en `app/services/calculo_cargo.py`, como funcion pura»,
pide probar la funcion sin base ni cliente HTTP, porque es donde vive el
riesgo (que celda de la tabla, un solo porcentaje, el redondeo). Las reglas
salen de `openspec/changes/cobro/specs/cargos/spec.md`, Requirements «Un
unico porcentaje sobre la tarifa base» y «El tramo de hijos del Mes», y de
`docs/prd/aclaraciones-cliente.md`, seccion 5.

La tabla de descuentos es la del contexto comun de HU-CC-01
(`5-historias-de-usuario.md`):

    | Categoria | Dia | Semana | Quincena | Mes 1 | Mes 2 | Mes 3 | Mes 4+ |
    | Socio     | 50  | 50     | 50       | 50    | 50    | 50    | 50     |
    | Empleado  | 10  | 10     | 10       | 10    | 15    | 20    | 25     |
    | No socio  | 0   | 0      | 0        | 0     | 10    | 15    | 20     |

Los enumerados se construyen por su valor (`CategoriaFamilia("no_socio")`),
que es el que fija la spec, para no depender del nombre de sus miembros.

Montos y porcentajes se comparan como `Decimal` exacto y, ademas, con
exponente -2: `Decimal("85000") == Decimal("85000.00")` es verdadero, y la
API tiene que devolver dos decimales.
"""

from decimal import Decimal

import pytest

from app.models.enums import CategoriaFamilia, Modalidad
from app.services.calculo_cargo import (
    Desglose,
    FaltaDescuento,
    TablaDescuentos,
    calcular_abono,
    calcular_monto_fijo,
)

SOCIO = CategoriaFamilia("socio")
EMPLEADO = CategoriaFamilia("empleado")
NO_SOCIO = CategoriaFamilia("no_socio")

MES = Modalidad("mes")
QUINCENA = Modalidad("quincena")
SEMANA = Modalidad("semana")
DIA = Modalidad("dia")

_TABLA_HU_CC_01: dict[CategoriaFamilia, tuple[str, str, str, str, str, str, str]] = {
    # dia, semana, quincena, mes 1, mes 2, mes 3, mes 4 o mas
    SOCIO: ("50.00", "50.00", "50.00", "50.00", "50.00", "50.00", "50.00"),
    EMPLEADO: ("10.00", "10.00", "10.00", "10.00", "15.00", "20.00", "25.00"),
    NO_SOCIO: ("0.00", "0.00", "0.00", "0.00", "10.00", "15.00", "20.00"),
}


def _por_modalidad() -> dict[tuple[CategoriaFamilia, Modalidad], Decimal]:
    celdas: dict[tuple[CategoriaFamilia, Modalidad], Decimal] = {}
    for categoria, fila in _TABLA_HU_CC_01.items():
        celdas[(categoria, DIA)] = Decimal(fila[0])
        celdas[(categoria, SEMANA)] = Decimal(fila[1])
        celdas[(categoria, QUINCENA)] = Decimal(fila[2])
    return celdas


def _mes() -> dict[tuple[CategoriaFamilia, int], Decimal]:
    celdas: dict[tuple[CategoriaFamilia, int], Decimal] = {}
    for categoria, fila in _TABLA_HU_CC_01.items():
        for tramo in (1, 2, 3, 4):
            celdas[(categoria, tramo)] = Decimal(fila[2 + tramo])
    return celdas


def _tabla(
    *,
    por_modalidad: dict[tuple[CategoriaFamilia, Modalidad], Decimal] | None = None,
    mes: dict[tuple[CategoriaFamilia, int], Decimal] | None = None,
) -> TablaDescuentos:
    return TablaDescuentos(
        por_modalidad=_por_modalidad() if por_modalidad is None else por_modalidad,
        mes=_mes() if mes is None else mes,
    )


def _exacto(valor: Decimal, esperado: str) -> None:
    """Igualdad exacta y con dos decimales."""
    assert isinstance(valor, Decimal), f"{valor!r} no es Decimal"
    assert valor == Decimal(esperado), f"{valor} != {esperado}"
    assert valor.as_tuple().exponent == -2, f"{valor} no tiene dos decimales"


def _abono(
    *,
    tarifa_base: str,
    categoria: CategoriaFamilia,
    modalidad: Modalidad,
    cantidad_hijos: int | None,
    descuentos: TablaDescuentos | None = None,
) -> Desglose:
    return calcular_abono(
        tarifa_base=Decimal(tarifa_base),
        categoria=categoria,
        modalidad=modalidad,
        cantidad_hijos=cantidad_hijos,
        descuentos=_tabla() if descuentos is None else descuentos,
    )


# --- Requirement: El tramo de hijos del Mes ---------------------------------


@pytest.mark.parametrize(
    ("hijos", "porcentaje", "total"),
    [
        (1, "10.00", "90000.00"),
        (2, "15.00", "85000.00"),
        (3, "20.00", "80000.00"),
    ],
)
def test_en_el_mes_el_porcentaje_es_el_del_tramo_de_hijos(
    hijos: int, porcentaje: str, total: str
) -> None:
    desglose = _abono(
        tarifa_base="100000.00", categoria=EMPLEADO, modalidad=MES, cantidad_hijos=hijos
    )

    assert desglose.categoria_aplicada == EMPLEADO
    assert desglose.cantidad_hijos_aplicada == hijos
    _exacto(desglose.monto_base, "100000.00")
    _exacto(desglose.porcentaje_aplicado, porcentaje)
    _exacto(desglose.monto_total, total)


def test_un_solo_hijo_no_toma_el_tramo_de_dos() -> None:
    desglose = _abono(tarifa_base="100000.00", categoria=NO_SOCIO, modalidad=MES, cantidad_hijos=1)

    assert desglose.cantidad_hijos_aplicada == 1
    _exacto(desglose.porcentaje_aplicado, "0.00")
    _exacto(desglose.monto_total, "100000.00")


@pytest.mark.parametrize("hijos", [4, 7])
def test_cuatro_o_mas_hijos_usan_el_tramo_de_cuatro(hijos: int) -> None:
    desglose = _abono(
        tarifa_base="100000.00", categoria=NO_SOCIO, modalidad=MES, cantidad_hijos=hijos
    )

    # El tramo es 4, pero la cantidad que se guarda es la contada.
    assert desglose.cantidad_hijos_aplicada == hijos
    _exacto(desglose.porcentaje_aplicado, "20.00")
    _exacto(desglose.monto_total, "80000.00")


def test_tres_hijos_no_toman_el_tramo_de_cuatro() -> None:
    # Caso de adentro del limite del tramo 4.
    desglose = _abono(tarifa_base="100000.00", categoria=NO_SOCIO, modalidad=MES, cantidad_hijos=3)

    assert desglose.cantidad_hijos_aplicada == 3
    _exacto(desglose.porcentaje_aplicado, "15.00")
    _exacto(desglose.monto_total, "85000.00")


@pytest.mark.parametrize("hijos", [None, 0])
def test_el_mes_sin_cantidad_de_hijos_es_un_error_de_programacion(
    hijos: int | None,
) -> None:
    with pytest.raises(ValueError):
        _abono(
            tarifa_base="100000.00",
            categoria=EMPLEADO,
            modalidad=MES,
            cantidad_hijos=hijos,
        )


# --- Requirement: Un unico porcentaje sobre la tarifa base -------------------


@pytest.mark.parametrize("hijos", [1, 3])
def test_en_la_semana_no_cuentan_los_hijos(hijos: int) -> None:
    desglose = _abono(
        tarifa_base="30000.00", categoria=EMPLEADO, modalidad=SEMANA, cantidad_hijos=hijos
    )

    assert desglose.categoria_aplicada == EMPLEADO
    assert desglose.cantidad_hijos_aplicada is None
    _exacto(desglose.monto_base, "30000.00")
    _exacto(desglose.porcentaje_aplicado, "10.00")
    _exacto(desglose.monto_total, "27000.00")


def test_quincena_de_la_tarde_usa_el_porcentaje_de_la_modalidad() -> None:
    desglose = _abono(tarifa_base="45000.00", categoria=SOCIO, modalidad=QUINCENA, cantidad_hijos=1)

    assert desglose.cantidad_hijos_aplicada is None
    _exacto(desglose.monto_base, "45000.00")
    _exacto(desglose.porcentaje_aplicado, "50.00")
    _exacto(desglose.monto_total, "22500.00")


def test_un_solo_porcentaje_nunca_acumulado() -> None:
    desglose = _abono(tarifa_base="100000.00", categoria=SOCIO, modalidad=MES, cantidad_hijos=4)

    _exacto(desglose.porcentaje_aplicado, "50.00")
    _exacto(desglose.monto_total, "50000.00")
    assert desglose.monto_total not in (Decimal("25000.00"), Decimal("0.00"))


def test_porcentaje_con_decimales() -> None:
    mes = _mes()
    mes[(EMPLEADO, 3)] = Decimal("36.25")

    desglose = _abono(
        tarifa_base="100000.00",
        categoria=EMPLEADO,
        modalidad=MES,
        cantidad_hijos=3,
        descuentos=_tabla(mes=mes),
    )

    _exacto(desglose.porcentaje_aplicado, "36.25")
    _exacto(desglose.monto_total, "63750.00")


def test_medio_centavo_se_redondea_hacia_arriba() -> None:
    desglose = _abono(tarifa_base="1000.05", categoria=SOCIO, modalidad=DIA, cantidad_hijos=None)

    _exacto(desglose.monto_base, "1000.05")
    _exacto(desglose.porcentaje_aplicado, "50.00")
    _exacto(desglose.monto_total, "500.03")


def test_menos_de_medio_centavo_se_redondea_hacia_abajo() -> None:
    # Caso de afuera del medio centavo: 100.06 al 10 es 90.054, que baja a
    # 90.05; con un redondeo hacia arriba siempre daria 90.06.
    desglose = _abono(tarifa_base="100.06", categoria=EMPLEADO, modalidad=DIA, cantidad_hijos=None)

    _exacto(desglose.porcentaje_aplicado, "10.00")
    _exacto(desglose.monto_total, "90.05")


def test_el_dia_no_devuelve_cantidad_de_hijos() -> None:
    desglose = _abono(tarifa_base="8000.00", categoria=EMPLEADO, modalidad=DIA, cantidad_hijos=2)

    assert desglose.cantidad_hijos_aplicada is None
    _exacto(desglose.porcentaje_aplicado, "10.00")
    _exacto(desglose.monto_total, "7200.00")


# --- Celda faltante -----------------------------------------------------------


def test_celda_faltante_del_mes_informa_categoria_y_tramo() -> None:
    mes = _mes()
    del mes[(EMPLEADO, 2)]

    with pytest.raises(FaltaDescuento) as error:
        _abono(
            tarifa_base="100000.00",
            categoria=EMPLEADO,
            modalidad=MES,
            cantidad_hijos=2,
            descuentos=_tabla(mes=mes),
        )

    assert error.value.categoria == EMPLEADO
    assert error.value.modalidad == MES
    assert error.value.tramo == 2


def test_celda_faltante_del_mes_con_seis_hijos_informa_el_tramo_cuatro() -> None:
    mes = _mes()
    del mes[(NO_SOCIO, 4)]

    with pytest.raises(FaltaDescuento) as error:
        _abono(
            tarifa_base="100000.00",
            categoria=NO_SOCIO,
            modalidad=MES,
            cantidad_hijos=6,
            descuentos=_tabla(mes=mes),
        )

    assert error.value.categoria == NO_SOCIO
    assert error.value.modalidad == MES
    assert error.value.tramo == 4


def test_celda_faltante_de_la_semana_informa_la_modalidad_sin_tramo() -> None:
    por_modalidad = _por_modalidad()
    del por_modalidad[(SOCIO, SEMANA)]

    with pytest.raises(FaltaDescuento) as error:
        _abono(
            tarifa_base="30000.00",
            categoria=SOCIO,
            modalidad=SEMANA,
            cantidad_hijos=None,
            descuentos=_tabla(por_modalidad=por_modalidad),
        )

    assert error.value.categoria == SOCIO
    assert error.value.modalidad == SEMANA
    assert error.value.tramo is None


def test_una_celda_faltante_de_otra_categoria_no_impide_el_calculo() -> None:
    # Caso de afuera: falta la celda de otra categoria, la pedida esta.
    mes = _mes()
    del mes[(SOCIO, 2)]

    desglose = _abono(
        tarifa_base="100000.00",
        categoria=EMPLEADO,
        modalidad=MES,
        cantidad_hijos=2,
        descuentos=_tabla(mes=mes),
    )

    _exacto(desglose.monto_total, "85000.00")


# --- Monto fijo ----------------------------------------------------------------


@pytest.mark.parametrize("categoria", [SOCIO, EMPLEADO, NO_SOCIO])
def test_el_monto_fijo_no_lleva_descuento(categoria: CategoriaFamilia) -> None:
    desglose = calcular_monto_fijo(monto_fijo=Decimal("20000.00"), categoria=categoria)

    assert desglose.categoria_aplicada == categoria
    assert desglose.cantidad_hijos_aplicada is None
    _exacto(desglose.monto_base, "20000.00")
    _exacto(desglose.porcentaje_aplicado, "0.00")
    _exacto(desglose.monto_total, "20000.00")
