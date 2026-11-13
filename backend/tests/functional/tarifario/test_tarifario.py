"""Capability `tarifario`: tarifa base, descuentos, periodos de cobro y tipos
de cargo.

Un test por Scenario de
`openspec/changes/tarifario-y-semilla/specs/tarifario/spec.md`.

Este change no expone nada por la API, asi que el contrato que se prueba es
el de la base: cada test inserta con SQL crudo sobre los nombres de
`3-modelo-de-datos.md` y comprueba que Postgres guarde o rechace la fila.

Cada insercion rechazada va dentro de `sesion.begin_nested()`, y cuando un
Scenario pide varias filas rechazadas se parametriza: el primer error
abortaria la transaccion y las demas filas no se llegarian a probar.

Montos y porcentajes se comparan como `Decimal` exacto: el dinero no lleva
tolerancia.
"""

from collections.abc import Mapping
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, Temporada

# --- preparacion -----------------------------------------------------------


@pytest.fixture
def temporada_2026_27(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


_INSERTAR_TARIFA = (
    "INSERT INTO tarifa_base (temporada_id, turno, modalidad, monto) "
    "VALUES (:t, :turno, :modalidad, :monto)"
)
_INSERTAR_DESCUENTO_MODALIDAD = (
    "INSERT INTO descuento_modalidad (temporada_id, categoria, modalidad, porcentaje) "
    "VALUES (:t, :categoria, :modalidad, :porcentaje)"
)
_INSERTAR_DESCUENTO_MES = (
    "INSERT INTO descuento_mes (temporada_id, categoria, tramo_hijos, porcentaje) "
    "VALUES (:t, :categoria, :tramo, :porcentaje)"
)
_INSERTAR_PERIODO = (
    "INSERT INTO periodo_cobro (temporada_id, modalidad, nombre, fecha_desde, fecha_hasta) "
    "VALUES (:t, :modalidad, :nombre, :desde, :hasta)"
)
_INSERTAR_TIPO_CARGO = (
    "INSERT INTO tipo_cargo (temporada_id, nombre, calculo, monto_fijo) "
    "VALUES (:t, :nombre, :calculo, :monto)"
)


def _insertar(sesion: Session, sql: str, parametros: Mapping[str, object]) -> None:
    sesion.execute(text(sql), parametros)


def _rechaza(sesion: Session, sql: str, parametros: Mapping[str, object]) -> None:
    """La insercion tiene que fallar en la base, aislada en un savepoint."""
    with pytest.raises(IntegrityError), sesion.begin_nested():
        sesion.execute(text(sql), parametros)


def _contar(sesion: Session, sql: str, parametros: Mapping[str, object]) -> int:
    return int(sesion.execute(text(sql), parametros).scalar_one())


def _es_decimal_exacto(valor: object, esperado: str) -> None:
    """Igual a `esperado`, como Decimal y con dos decimales guardados."""
    assert isinstance(valor, Decimal), f"Se leyo {type(valor).__name__}, no Decimal"
    assert valor == Decimal(esperado)
    assert valor.as_tuple().exponent == -2, f"{valor} no quedo con dos decimales"


# --- Requirement: Tarifa base por turno y modalidad ------------------------


class TestTarifaBase:
    def test_el_monto_minimo_positivo_queda_guardado_exacto(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: El monto minimo positivo (limite de adentro)
        _insertar(
            sesion,
            _INSERTAR_TARIFA,
            {
                "t": temporada_2026_27,
                "turno": "manana",
                "modalidad": "dia",
                "monto": Decimal("0.01"),
            },
        )
        monto = sesion.execute(
            text(
                "SELECT monto FROM tarifa_base "
                "WHERE temporada_id = :t AND turno = 'manana' AND modalidad = 'dia'"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(monto, "0.01")

    def test_la_base_rechaza_una_tarifa_de_monto_cero(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Monto cero (limite de afuera)
        _rechaza(
            sesion,
            _INSERTAR_TARIFA,
            {"t": temporada_2026_27, "turno": "manana", "modalidad": "dia", "monto": Decimal("0")},
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM tarifa_base WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_dos_tarifas_para_la_misma_combinacion(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Dos tarifas para la misma combinacion
        base = {"t": temporada_2026_27, "turno": "manana", "modalidad": "mes"}
        _insertar(sesion, _INSERTAR_TARIFA, {**base, "monto": Decimal("100000.00")})
        _rechaza(sesion, _INSERTAR_TARIFA, {**base, "monto": Decimal("90000.00")})
        monto = sesion.execute(
            text(
                "SELECT monto FROM tarifa_base "
                "WHERE temporada_id = :t AND turno = 'manana' AND modalidad = 'mes'"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(monto, "100000.00")


# --- Requirement: Descuento por categoria para Dia, Semana y Quincena ------


class TestDescuentoModalidad:
    def test_el_descuento_para_la_quincena_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Descuento para la Quincena
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MODALIDAD,
            {
                "t": temporada_2026_27,
                "categoria": "socio",
                "modalidad": "quincena",
                "porcentaje": Decimal("50.00"),
            },
        )
        porcentaje = sesion.execute(
            text(
                "SELECT porcentaje FROM descuento_modalidad "
                "WHERE temporada_id = :t AND categoria = 'socio' AND modalidad = 'quincena'"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(porcentaje, "50.00")

    def test_la_base_rechaza_un_descuento_por_modalidad_para_el_mes(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Descuento por modalidad para el Mes
        _rechaza(
            sesion,
            _INSERTAR_DESCUENTO_MODALIDAD,
            {
                "t": temporada_2026_27,
                "categoria": "socio",
                "modalidad": "mes",
                "porcentaje": Decimal("50.00"),
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM descuento_modalidad WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_dos_descuentos_para_la_misma_categoria_y_modalidad(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Dos descuentos para la misma categoria y modalidad
        base = {"t": temporada_2026_27, "categoria": "empleado", "modalidad": "semana"}
        _insertar(sesion, _INSERTAR_DESCUENTO_MODALIDAD, {**base, "porcentaje": Decimal("25.00")})
        _rechaza(sesion, _INSERTAR_DESCUENTO_MODALIDAD, {**base, "porcentaje": Decimal("30.00")})
        porcentaje = sesion.execute(
            text(
                "SELECT porcentaje FROM descuento_modalidad "
                "WHERE temporada_id = :t AND categoria = 'empleado' AND modalidad = 'semana'"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(porcentaje, "25.00")


# --- Requirement: Descuento del Mes por tramo de hijos ---------------------


class TestDescuentoMes:
    def test_los_tramos_de_los_extremos_quedan_guardados(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Los tramos de los extremos (limites de adentro: 1 y 4)
        for tramo in (1, 4):
            _insertar(
                sesion,
                _INSERTAR_DESCUENTO_MES,
                {
                    "t": temporada_2026_27,
                    "categoria": "no_socio",
                    "tramo": tramo,
                    "porcentaje": Decimal("0.00"),
                },
            )
        tramos = {
            f[0]
            for f in sesion.execute(
                text(
                    "SELECT tramo_hijos FROM descuento_mes "
                    "WHERE temporada_id = :t AND categoria = 'no_socio'"
                ),
                {"t": temporada_2026_27},
            )
        }
        assert tramos == {1, 4}

    @pytest.mark.parametrize("tramo", [0, 5], ids=["tramo_0", "tramo_5"])
    def test_la_base_rechaza_los_tramos_fuera_de_rango(
        self, sesion: Session, temporada_2026_27: int, tramo: int
    ) -> None:
        # Scenario: Tramos fuera de rango (limites de afuera: 0 y 5), una fila por caso
        _rechaza(
            sesion,
            _INSERTAR_DESCUENTO_MES,
            {
                "t": temporada_2026_27,
                "categoria": "no_socio",
                "tramo": tramo,
                "porcentaje": Decimal("0.00"),
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM descuento_mes WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_dos_descuentos_para_la_misma_categoria_y_tramo(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Dos descuentos para la misma categoria y tramo
        base = {"t": temporada_2026_27, "categoria": "socio", "tramo": 2}
        _insertar(sesion, _INSERTAR_DESCUENTO_MES, {**base, "porcentaje": Decimal("55.00")})
        _rechaza(sesion, _INSERTAR_DESCUENTO_MES, {**base, "porcentaje": Decimal("60.00")})
        porcentaje = sesion.execute(
            text(
                "SELECT porcentaje FROM descuento_mes "
                "WHERE temporada_id = :t AND categoria = 'socio' AND tramo_hijos = 2"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(porcentaje, "55.00")


# --- Requirement: Los porcentajes van de 0 a 100 con dos decimales exactos -


class TestPorcentajes:
    def test_los_porcentajes_en_los_extremos_quedan_guardados(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Porcentajes en los extremos (limites de adentro: 0.00 y 100.00)
        t = temporada_2026_27
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MODALIDAD,
            {"t": t, "categoria": "socio", "modalidad": "dia", "porcentaje": Decimal("0.00")},
        )
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MODALIDAD,
            {"t": t, "categoria": "socio", "modalidad": "semana", "porcentaje": Decimal("100.00")},
        )
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MES,
            {"t": t, "categoria": "socio", "tramo": 1, "porcentaje": Decimal("0.00")},
        )
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MES,
            {"t": t, "categoria": "socio", "tramo": 2, "porcentaje": Decimal("100.00")},
        )

        por_modalidad = dict(
            sesion.execute(
                text(
                    "SELECT modalidad::text, porcentaje FROM descuento_modalidad "
                    "WHERE temporada_id = :t AND categoria = 'socio'"
                ),
                {"t": t},
            ).all()
        )
        assert set(por_modalidad) == {"dia", "semana"}
        _es_decimal_exacto(por_modalidad["dia"], "0.00")
        _es_decimal_exacto(por_modalidad["semana"], "100.00")

        por_tramo = dict(
            sesion.execute(
                text(
                    "SELECT tramo_hijos, porcentaje FROM descuento_mes "
                    "WHERE temporada_id = :t AND categoria = 'socio'"
                ),
                {"t": t},
            ).all()
        )
        assert set(por_tramo) == {1, 2}
        _es_decimal_exacto(por_tramo[1], "0.00")
        _es_decimal_exacto(por_tramo[2], "100.00")

    @pytest.mark.parametrize(
        ("sql", "fila"),
        [
            (
                _INSERTAR_DESCUENTO_MODALIDAD,
                {"categoria": "socio", "modalidad": "dia", "porcentaje": Decimal("-0.01")},
            ),
            (
                _INSERTAR_DESCUENTO_MODALIDAD,
                {"categoria": "socio", "modalidad": "dia", "porcentaje": Decimal("100.01")},
            ),
            (
                _INSERTAR_DESCUENTO_MES,
                {"categoria": "socio", "tramo": 1, "porcentaje": Decimal("-0.01")},
            ),
            (
                _INSERTAR_DESCUENTO_MES,
                {"categoria": "socio", "tramo": 1, "porcentaje": Decimal("100.01")},
            ),
        ],
        ids=[
            "descuento_modalidad_-0.01",
            "descuento_modalidad_100.01",
            "descuento_mes_-0.01",
            "descuento_mes_100.01",
        ],
    )
    def test_la_base_rechaza_los_porcentajes_fuera_de_rango(
        self,
        sesion: Session,
        temporada_2026_27: int,
        sql: str,
        fila: dict[str, object],
    ) -> None:
        # Scenario: Porcentajes fuera de rango (limites de afuera), una fila por caso
        _rechaza(sesion, sql, {"t": temporada_2026_27, **fila})

    def test_un_porcentaje_con_dos_decimales_se_relee_exacto(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Un porcentaje con dos decimales
        _insertar(
            sesion,
            _INSERTAR_DESCUENTO_MES,
            {
                "t": temporada_2026_27,
                "categoria": "empleado",
                "tramo": 3,
                "porcentaje": Decimal("36.25"),
            },
        )
        porcentaje = sesion.execute(
            text(
                "SELECT porcentaje FROM descuento_mes "
                "WHERE temporada_id = :t AND categoria = 'empleado' AND tramo_hijos = 3"
            ),
            {"t": temporada_2026_27},
        ).scalar_one()
        _es_decimal_exacto(porcentaje, "36.25")


# --- Requirement: Periodos de cobro con fechas fijas -----------------------


class TestPeriodoCobro:
    def test_un_periodo_de_un_solo_dia_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Periodo de un solo dia (limite de adentro)
        _insertar(
            sesion,
            _INSERTAR_PERIODO,
            {
                "t": temporada_2026_27,
                "modalidad": "semana",
                "nombre": "Semana 1",
                "desde": date(2027, 1, 4),
                "hasta": date(2027, 1, 4),
            },
        )
        fila = sesion.execute(
            text(
                "SELECT fecha_desde, fecha_hasta FROM periodo_cobro "
                "WHERE temporada_id = :t AND modalidad = 'semana' AND nombre = 'Semana 1'"
            ),
            {"t": temporada_2026_27},
        ).one()
        assert fila[0] == date(2027, 1, 4)
        assert fila[1] == date(2027, 1, 4)

    def test_la_base_rechaza_un_periodo_con_las_fechas_invertidas(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Periodo con las fechas invertidas (limite de afuera)
        _rechaza(
            sesion,
            _INSERTAR_PERIODO,
            {
                "t": temporada_2026_27,
                "modalidad": "semana",
                "nombre": "Semana 1",
                "desde": date(2027, 1, 5),
                "hasta": date(2027, 1, 4),
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM periodo_cobro WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_un_periodo_para_la_modalidad_dia(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Periodo para la modalidad Dia
        _rechaza(
            sesion,
            _INSERTAR_PERIODO,
            {
                "t": temporada_2026_27,
                "modalidad": "dia",
                "nombre": "Día 1",
                "desde": date(2027, 1, 4),
                "hasta": date(2027, 1, 4),
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM periodo_cobro WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_un_nombre_repetido_en_la_misma_modalidad(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Nombre repetido en la misma modalidad
        base = {"t": temporada_2026_27, "modalidad": "mes", "nombre": "Mes 1"}
        _insertar(
            sesion,
            _INSERTAR_PERIODO,
            {**base, "desde": date(2027, 1, 4), "hasta": date(2027, 1, 31)},
        )
        _rechaza(
            sesion,
            _INSERTAR_PERIODO,
            {**base, "desde": date(2027, 2, 1), "hasta": date(2027, 2, 28)},
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM periodo_cobro "
                "WHERE temporada_id = :t AND modalidad = 'mes' AND nombre = 'Mes 1'",
                {"t": temporada_2026_27},
            )
            == 1
        )

    def test_el_mismo_nombre_en_otra_modalidad_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: El mismo nombre en otra modalidad
        fechas = {"desde": date(2027, 1, 4), "hasta": date(2027, 1, 17)}
        _insertar(
            sesion,
            _INSERTAR_PERIODO,
            {"t": temporada_2026_27, "modalidad": "mes", "nombre": "Período 1", **fechas},
        )
        _insertar(
            sesion,
            _INSERTAR_PERIODO,
            {"t": temporada_2026_27, "modalidad": "quincena", "nombre": "Período 1", **fechas},
        )
        modalidades = {
            f[0]
            for f in sesion.execute(
                text(
                    "SELECT modalidad::text FROM periodo_cobro "
                    "WHERE temporada_id = :t AND nombre = 'Período 1'"
                ),
                {"t": temporada_2026_27},
            )
        }
        assert modalidades == {"mes", "quincena"}


# --- Requirement: Tipos de cargo de monto fijo o por tarifario -------------


class TestTipoCargo:
    def test_un_tipo_de_monto_fijo_con_su_monto_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Tipo de monto fijo con su monto
        _insertar(
            sesion,
            _INSERTAR_TIPO_CARGO,
            {
                "t": temporada_2026_27,
                "nombre": "Preinscripción",
                "calculo": "monto_fijo",
                "monto": Decimal("20000.00"),
            },
        )
        fila = sesion.execute(
            text(
                "SELECT calculo::text, monto_fijo FROM tipo_cargo "
                "WHERE temporada_id = :t AND nombre = 'Preinscripción'"
            ),
            {"t": temporada_2026_27},
        ).one()
        assert fila[0] == "monto_fijo"
        _es_decimal_exacto(fila[1], "20000.00")

    def test_la_base_rechaza_un_tipo_de_monto_fijo_sin_monto(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Tipo de monto fijo sin monto
        _rechaza(
            sesion,
            _INSERTAR_TIPO_CARGO,
            {
                "t": temporada_2026_27,
                "nombre": "Preinscripción",
                "calculo": "monto_fijo",
                "monto": None,
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM tipo_cargo WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_la_base_rechaza_un_tipo_por_tarifario_con_monto(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Tipo por tarifario con monto
        _rechaza(
            sesion,
            _INSERTAR_TIPO_CARGO,
            {
                "t": temporada_2026_27,
                "nombre": "Abono",
                "calculo": "tarifario",
                "monto": Decimal("20000.00"),
            },
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM tipo_cargo WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )

    def test_un_tipo_por_tarifario_sin_monto_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Tipo por tarifario sin monto
        _insertar(
            sesion,
            _INSERTAR_TIPO_CARGO,
            {"t": temporada_2026_27, "nombre": "Abono", "calculo": "tarifario", "monto": None},
        )
        fila = sesion.execute(
            text(
                "SELECT calculo::text, monto_fijo FROM tipo_cargo "
                "WHERE temporada_id = :t AND nombre = 'Abono'"
            ),
            {"t": temporada_2026_27},
        ).one()
        assert fila[0] == "tarifario"
        assert fila[1] is None

    def test_la_base_rechaza_un_nombre_repetido_en_la_misma_temporada(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Nombre repetido en la misma temporada
        abono = {"t": temporada_2026_27, "nombre": "Abono", "calculo": "tarifario", "monto": None}
        _insertar(sesion, _INSERTAR_TIPO_CARGO, abono)
        _rechaza(sesion, _INSERTAR_TIPO_CARGO, abono)
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM tipo_cargo WHERE temporada_id = :t AND nombre = 'Abono'",
                {"t": temporada_2026_27},
            )
            == 1
        )
