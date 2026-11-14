"""Capability `cargos`: las restricciones de la tabla `cargo`.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirements «El cargo guarda su calculo», «La forma del cargo segun el tipo
y la modalidad» y «Un cargo no se repite».

Los endpoints todavia no existen, asi que el contrato que se prueba es el de
la base: cada test inserta con SQL crudo sobre las columnas de
`3-modelo-de-datos.md` («`cargo`») y comprueba que Postgres guarde o rechace
la fila. Los nombres de las restricciones que se esperan son los de
`openspec/changes/cobro/design.md`, seccion «Esquema»: mirar cual salto es
lo que asegura que la fila se rechazo por la regla del Scenario y no por
otra cosa (una FK mal armada en la preparacion, por ejemplo).

Cada fila de un test de rechazo es valida en todo lo demas: si el Scenario
habla del porcentaje, el total es el que corresponde a ese porcentaje, y asi.

Cada sentencia rechazada va dentro de `sesion.begin_nested()`: si no, el
error aborta la transaccion y lo que se comprueba despues no corre.

Montos y porcentajes se comparan como `Decimal` exacto.
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
    inscribir,
    insertar_grupo,
)

# --- preparacion -----------------------------------------------------------


@dataclass(frozen=True)
class Escenario:
    temporada: int
    admin: int
    familia_perez: int
    juan: int
    ana: int
    juan_delfines_manana: int
    mes_1: int
    mes_2: int
    semana_1: int
    preinscripcion: int
    abono: int


def _periodo(
    sesion: Session, temporada_id: int, modalidad: str, nombre: str, desde: date, hasta: date
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO periodo_cobro "
                "(temporada_id, modalidad, nombre, fecha_desde, fecha_hasta) "
                "VALUES (:t, :m, :n, :d, :h) RETURNING id"
            ),
            {"t": temporada_id, "m": modalidad, "n": nombre, "d": desde, "h": hasta},
        ).scalar_one()
    )


def _tipo_cargo(
    sesion: Session, temporada_id: int, nombre: str, calculo: str, monto: Decimal | None
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO tipo_cargo (temporada_id, nombre, calculo, monto_fijo) "
                "VALUES (:t, :n, :c, :m) RETURNING id"
            ),
            {"t": temporada_id, "n": nombre, "c": calculo, "m": monto},
        ).scalar_one()
    )


@pytest.fixture
def esc(sesion: Session) -> Escenario:
    """Temporada 2026-27 con la familia Perez (empleado): Juan inscripto en
    «Delfines» manana y Ana, su hermana. Periodos «Mes 1», «Mes 2» y
    «Semana 1», y los tipos «Preinscripcion» (monto fijo) y «Abono»."""
    temporada = crear_vigente(sesion)
    admin = crear_usuario(sesion, "admin", RolUsuario.ADMIN)
    familia = crear_familia(sesion, "empleado")
    juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia, nacimiento=date(2020, 3, 10))
    ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=familia, nacimiento=date(2018, 5, 2))
    delfines = insertar_grupo(sesion, temporada, "Delfines", "manana")
    inscripcion = inscribir(sesion, juan, delfines, temporada, "manana", admin)
    return Escenario(
        temporada=temporada,
        admin=admin,
        familia_perez=familia,
        juan=juan,
        ana=ana,
        juan_delfines_manana=inscripcion,
        mes_1=_periodo(sesion, temporada, "mes", "Mes 1", date(2027, 1, 4), date(2027, 1, 29)),
        mes_2=_periodo(sesion, temporada, "mes", "Mes 2", date(2027, 2, 1), date(2027, 2, 26)),
        semana_1=_periodo(
            sesion, temporada, "semana", "Semana 1", date(2027, 1, 4), date(2027, 1, 8)
        ),
        preinscripcion=_tipo_cargo(
            sesion, temporada, "Preinscripción", "monto_fijo", Decimal("20000.00")
        ),
        abono=_tipo_cargo(sesion, temporada, "Abono", "tarifario", None),
    )


# `creado_en` va con now() explicito para no depender de que la columna
# tenga un valor por defecto: eso no es lo que prueba este archivo.
_INSERTAR_CARGO = (
    "INSERT INTO cargo ("
    "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
    "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
    "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
    ") VALUES ("
    ":temporada_id, :familia_id, :alumno_id, :tipo_cargo_id, :inscripcion_id, :modalidad, "
    ":periodo_cobro_id, :fecha_dia, :categoria_aplicada, :cantidad_hijos_aplicada, "
    ":monto_base, :porcentaje_aplicado, :monto_total, :creado_por, now()"
    ")"
)


def _abono_mes(esc: Escenario, **cambios: object) -> dict[str, object]:
    """Un Abono del Mes valido de Juan, manana, «Mes 1», 2 hijos al 15 %.
    `cambios` pisa las columnas que el test necesita distintas."""
    fila: dict[str, object] = {
        "temporada_id": esc.temporada,
        "familia_id": esc.familia_perez,
        "alumno_id": esc.juan,
        "tipo_cargo_id": esc.abono,
        "inscripcion_id": esc.juan_delfines_manana,
        "modalidad": "mes",
        "periodo_cobro_id": esc.mes_1,
        "fecha_dia": None,
        "categoria_aplicada": "empleado",
        "cantidad_hijos_aplicada": 2,
        "monto_base": Decimal("100000.00"),
        "porcentaje_aplicado": Decimal("15.00"),
        "monto_total": Decimal("85000.00"),
        "creado_por": esc.admin,
    }
    fila.update(cambios)
    return fila


def _abono_dia(esc: Escenario, fecha: date, **cambios: object) -> dict[str, object]:
    """Un Abono del Dia valido de Juan, manana, 8000.00 al 10 %."""
    base = {
        "modalidad": "dia",
        "periodo_cobro_id": None,
        "fecha_dia": fecha,
        "cantidad_hijos_aplicada": None,
        "monto_base": Decimal("8000.00"),
        "porcentaje_aplicado": Decimal("10.00"),
        "monto_total": Decimal("7200.00"),
    }
    base.update(cambios)
    return _abono_mes(esc, **base)


def _monto_fijo(esc: Escenario, **cambios: object) -> dict[str, object]:
    """Una Preinscripcion valida de Juan: 20000.00 sin descuento, sin
    inscripcion, modalidad, periodo, fecha ni cantidad de hijos."""
    base = {
        "tipo_cargo_id": esc.preinscripcion,
        "inscripcion_id": None,
        "modalidad": None,
        "periodo_cobro_id": None,
        "fecha_dia": None,
        "cantidad_hijos_aplicada": None,
        "monto_base": Decimal("20000.00"),
        "porcentaje_aplicado": Decimal("0.00"),
        "monto_total": Decimal("20000.00"),
    }
    base.update(cambios)
    return _abono_mes(esc, **base)


def _insertar(sesion: Session, fila: Mapping[str, object]) -> None:
    sesion.execute(text(_INSERTAR_CARGO), fila)


def _rechaza(sesion: Session, fila: Mapping[str, object], *restricciones: str) -> None:
    """La fila tiene que fallar en la base, aislada en un savepoint, por una
    de `restricciones`."""
    with pytest.raises(IntegrityError) as error, sesion.begin_nested():
        sesion.execute(text(_INSERTAR_CARGO), fila)
    assert error.value.orig is not None
    nombre = error.value.orig.diag.constraint_name  # type: ignore[union-attr]
    assert nombre in restricciones, f"Salto {nombre!r}, se esperaba {restricciones}"


def _contar_cargos(sesion: Session) -> int:
    return int(sesion.execute(text("SELECT count(*) FROM cargo")).scalar_one())


def _es_decimal_exacto(valor: object, esperado: str) -> None:
    assert isinstance(valor, Decimal), f"Se leyo {type(valor).__name__}, no Decimal"
    assert valor == Decimal(esperado)
    assert valor.as_tuple().exponent == -2, f"{valor} no quedo con dos decimales"


# --- Requirement: El cargo guarda su calculo -------------------------------


class TestElCargoGuardaSuCalculo:
    def test_un_cargo_con_total_coherente_queda_guardado_con_su_calculo(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Total coherente con la base y el porcentaje
        _insertar(sesion, _abono_mes(esc))

        fila = sesion.execute(
            text(
                "SELECT temporada_id, familia_id, alumno_id, tipo_cargo_id, "
                "categoria_aplicada::text AS categoria, cantidad_hijos_aplicada, "
                "monto_base, porcentaje_aplicado, monto_total, creado_por "
                "FROM cargo"
            )
        ).one()
        assert fila.temporada_id == esc.temporada
        assert fila.familia_id == esc.familia_perez
        assert fila.alumno_id == esc.juan
        assert fila.tipo_cargo_id == esc.abono
        assert fila.categoria == "empleado"
        assert fila.cantidad_hijos_aplicada == 2
        assert fila.creado_por == esc.admin
        _es_decimal_exacto(fila.monto_base, "100000.00")
        _es_decimal_exacto(fila.porcentaje_aplicado, "15.00")
        _es_decimal_exacto(fila.monto_total, "85000.00")

    def test_la_base_rechaza_un_total_que_no_corresponde_a_la_base_y_el_porcentaje(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Total que no corresponde (un centavo de mas)
        _rechaza(sesion, _abono_mes(esc, monto_total=Decimal("85000.01")), "ck_cargo_total")

        assert _contar_cargos(sesion) == 0

    def test_la_base_rechaza_un_porcentaje_por_encima_de_100_y_uno_por_debajo_de_0(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Porcentaje fuera de rango
        # El total de cada fila es el que da la formula con ese porcentaje,
        # para que lo unico fuera de regla sea el porcentaje:
        # 100000.00 * (1 - 100.01/100) = -10.00; 100000.00 * (1 + 0.01/100) = 100010.00
        _rechaza(
            sesion,
            _abono_mes(
                esc,
                porcentaje_aplicado=Decimal("100.01"),
                monto_total=Decimal("-10.00"),
            ),
            "ck_cargo_porcentaje_rango",
        )
        _rechaza(
            sesion,
            _abono_mes(
                esc,
                porcentaje_aplicado=Decimal("-0.01"),
                monto_total=Decimal("100010.00"),
            ),
            "ck_cargo_porcentaje_rango",
        )

        assert _contar_cargos(sesion) == 0


# --- Requirement: La forma del cargo segun el tipo y la modalidad ----------


class TestLaFormaDelCargo:
    def test_un_cargo_de_monto_fijo_sin_datos_del_abono_queda_guardado(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Cargo de monto fijo
        _insertar(sesion, _monto_fijo(esc))

        fila = sesion.execute(
            text(
                "SELECT inscripcion_id, modalidad, periodo_cobro_id, fecha_dia, "
                "cantidad_hijos_aplicada, monto_base, porcentaje_aplicado, monto_total "
                "FROM cargo"
            )
        ).one()
        assert fila.inscripcion_id is None
        assert fila.modalidad is None
        assert fila.periodo_cobro_id is None
        assert fila.fecha_dia is None
        assert fila.cantidad_hijos_aplicada is None
        _es_decimal_exacto(fila.monto_base, "20000.00")
        _es_decimal_exacto(fila.porcentaje_aplicado, "0.00")
        _es_decimal_exacto(fila.monto_total, "20000.00")

    def test_la_base_rechaza_un_cargo_de_monto_fijo_con_periodo(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Cargo de monto fijo con periodo
        _rechaza(
            sesion,
            _monto_fijo(esc, periodo_cobro_id=esc.mes_1),
            "ck_cargo_monto_fijo_sin_abono",
        )

        assert _contar_cargos(sesion) == 0

    def test_la_base_rechaza_un_mes_sin_cantidad_de_hijos(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Mes sin cantidad de hijos
        _rechaza(
            sesion,
            _abono_mes(esc, cantidad_hijos_aplicada=None),
            "ck_cargo_hijos_solo_mes",
        )

        assert _contar_cargos(sesion) == 0

    def test_la_base_rechaza_una_semana_con_cantidad_de_hijos(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Semana con cantidad de hijos
        _rechaza(
            sesion,
            _abono_mes(
                esc,
                modalidad="semana",
                periodo_cobro_id=esc.semana_1,
                cantidad_hijos_aplicada=2,
                monto_base=Decimal("30000.00"),
                porcentaje_aplicado=Decimal("10.00"),
                monto_total=Decimal("27000.00"),
            ),
            "ck_cargo_hijos_solo_mes",
        )

        assert _contar_cargos(sesion) == 0

    def test_la_base_rechaza_una_cantidad_de_hijos_cero(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Cantidad de hijos cero. El caso de adentro (una cantidad
        # positiva en el Mes) queda guardado en «Total coherente», con 2.
        _rechaza(
            sesion,
            _abono_mes(esc, cantidad_hijos_aplicada=0),
            "ck_cargo_hijos_positivo",
        )

        assert _contar_cargos(sesion) == 0

    def test_la_base_rechaza_un_periodo_de_otra_modalidad(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Periodo de otra modalidad
        _rechaza(
            sesion,
            _abono_mes(esc, periodo_cobro_id=esc.semana_1),
            "fk_cargo_periodo_cobro",
        )

        assert _contar_cargos(sesion) == 0

    def test_un_dia_con_fecha_y_sin_periodo_queda_guardado(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Dia con fecha
        _insertar(sesion, _abono_dia(esc, date(2027, 1, 5)))

        fila = sesion.execute(
            text(
                "SELECT modalidad::text AS modalidad, fecha_dia, periodo_cobro_id, "
                "cantidad_hijos_aplicada, monto_total FROM cargo"
            )
        ).one()
        assert fila.modalidad == "dia"
        assert fila.fecha_dia == date(2027, 1, 5)
        assert fila.periodo_cobro_id is None
        assert fila.cantidad_hijos_aplicada is None
        _es_decimal_exacto(fila.monto_total, "7200.00")

    def test_la_base_rechaza_un_dia_con_periodo(self, sesion: Session, esc: Escenario) -> None:
        # Scenario: Dia con periodo
        # Con modalidad `dia`, el periodo «Semana 1» viola dos reglas a la
        # vez: la forma (Dia no lleva periodo) y la FK compuesta (el periodo
        # no es de modalidad `dia`). Cualquiera de las dos es un rechazo valido.
        _rechaza(
            sesion,
            _abono_dia(esc, date(2027, 1, 5), periodo_cobro_id=esc.semana_1),
            "ck_cargo_periodo_o_fecha",
            "fk_cargo_periodo_cobro",
        )

        assert _contar_cargos(sesion) == 0


# --- Requirement: Un cargo no se repite ------------------------------------


class TestUnCargoNoSeRepite:
    def test_la_base_rechaza_un_segundo_cargo_de_la_misma_inscripcion_y_periodo(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Mismo periodo en la misma inscripcion
        _insertar(sesion, _abono_mes(esc))

        _rechaza(sesion, _abono_mes(esc), "uq_cargo_inscripcion_periodo")

        assert _contar_cargos(sesion) == 1

    def test_un_cargo_de_la_misma_inscripcion_por_otro_periodo_queda_guardado(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Otro periodo en la misma inscripcion
        _insertar(sesion, _abono_mes(esc))

        _insertar(sesion, _abono_mes(esc, periodo_cobro_id=esc.mes_2))

        periodos = sesion.execute(
            text(
                "SELECT periodo_cobro_id FROM cargo WHERE inscripcion_id = :i "
                "ORDER BY periodo_cobro_id"
            ),
            {"i": esc.juan_delfines_manana},
        ).scalars()
        assert sorted(periodos) == sorted([esc.mes_1, esc.mes_2])

    def test_la_base_rechaza_un_segundo_cargo_dia_de_la_misma_inscripcion_y_fecha(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: El mismo dia en la misma inscripcion
        _insertar(sesion, _abono_dia(esc, date(2027, 1, 5)))

        _rechaza(sesion, _abono_dia(esc, date(2027, 1, 5)), "uq_cargo_inscripcion_fecha")

        assert _contar_cargos(sesion) == 1

    def test_la_base_rechaza_un_segundo_cargo_de_monto_fijo_del_mismo_tipo_para_el_alumno(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: Dos cargos de monto fijo del mismo tipo para el mismo alumno
        _insertar(sesion, _monto_fijo(esc))

        _rechaza(sesion, _monto_fijo(esc), "uq_cargo_alumno_tipo_monto_fijo")

        assert _contar_cargos(sesion) == 1

    def test_el_mismo_cargo_de_monto_fijo_para_un_hermano_queda_guardado(
        self, sesion: Session, esc: Escenario
    ) -> None:
        # Scenario: El mismo cargo de monto fijo para un hermano
        _insertar(sesion, _monto_fijo(esc))

        _insertar(sesion, _monto_fijo(esc, alumno_id=esc.ana))

        alumnos = sesion.execute(
            text("SELECT alumno_id FROM cargo WHERE tipo_cargo_id = :t"),
            {"t": esc.preinscripcion},
        ).scalars()
        assert sorted(alumnos) == sorted([esc.juan, esc.ana])
