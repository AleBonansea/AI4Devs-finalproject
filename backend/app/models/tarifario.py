"""El tarifario de la temporada: tarifa base, descuentos, periodos de cobro
y tipos de cargo.

Todo cuelga de `temporada`: cada verano tiene su propio tarifario. Montos en
Numeric(12, 2) y porcentajes en Numeric(5, 2), leidos como Decimal: el
calculo del cargo multiplica con ellos y un float no relee exacto.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import (
    TIPO_CALCULO_CARGO,
    TIPO_CATEGORIA_FAMILIA,
    TIPO_MODALIDAD,
    TIPO_TURNO,
    CalculoCargo,
    CategoriaFamilia,
    Modalidad,
    Turno,
)


class TarifaBase(MarcaDeCreacion, Base):
    """El precio sin descuento por turno y modalidad."""

    __tablename__ = "tarifa_base"

    temporada_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    turno: Mapped[Turno] = mapped_column(TIPO_TURNO, primary_key=True)
    modalidad: Mapped[Modalidad] = mapped_column(TIPO_MODALIDAD, primary_key=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_tarifa_base_temporada"),
        CheckConstraint("monto > 0", name="ck_tarifa_base_monto_positivo"),
    )


class DescuentoModalidad(MarcaDeCreacion, Base):
    """Un % por categoria para Dia, Semana y Quincena. El Mes va aparte, en
    `descuento_mes`: asi ningun cargo encuentra dos porcentajes."""

    __tablename__ = "descuento_modalidad"

    temporada_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    categoria: Mapped[CategoriaFamilia] = mapped_column(TIPO_CATEGORIA_FAMILIA, primary_key=True)
    modalidad: Mapped[Modalidad] = mapped_column(TIPO_MODALIDAD, primary_key=True)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["temporada_id"], ["temporada.id"], name="fk_descuento_modalidad_temporada"
        ),
        CheckConstraint("modalidad <> 'mes'", name="ck_descuento_modalidad_no_mes"),
        CheckConstraint(
            "porcentaje BETWEEN 0 AND 100", name="ck_descuento_modalidad_porcentaje_rango"
        ),
    )


class DescuentoMes(MarcaDeCreacion, Base):
    """Un % por categoria y tramo de hijos, solo para el Mes."""

    __tablename__ = "descuento_mes"

    temporada_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    categoria: Mapped[CategoriaFamilia] = mapped_column(TIPO_CATEGORIA_FAMILIA, primary_key=True)
    # El tramo 4 significa "4 o mas".
    tramo_hijos: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_descuento_mes_temporada"),
        CheckConstraint("tramo_hijos BETWEEN 1 AND 4", name="ck_descuento_mes_tramo_rango"),
        CheckConstraint("porcentaje BETWEEN 0 AND 100", name="ck_descuento_mes_porcentaje_rango"),
    )


class PeriodoCobro(MarcaDeCreacion, Base):
    """Las fechas fijas de cada Mes, Quincena y Semana. El Dia no tiene
    rango: el cargo guarda la fecha."""

    __tablename__ = "periodo_cobro"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    modalidad: Mapped[Modalidad] = mapped_column(TIPO_MODALIDAD, nullable=False)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_hasta: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_periodo_cobro_temporada"),
        CheckConstraint("modalidad <> 'dia'", name="ck_periodo_cobro_no_dia"),
        CheckConstraint("fecha_desde <= fecha_hasta", name="ck_periodo_cobro_fechas"),
        UniqueConstraint(
            "temporada_id",
            "modalidad",
            "nombre",
            name="uq_periodo_cobro_temporada_modalidad_nombre",
        ),
        # Redundante como unicidad, pero es la clave a la que apunta la FK
        # compuesta de `cargo`: asi un cargo no puede caer en un periodo de
        # otra modalidad.
        UniqueConstraint("id", "modalidad", name="uq_periodo_cobro_id_modalidad"),
    )


class TipoCargo(MarcaDeCreacion, Base):
    """Catalogo de tipos de cargo de la temporada (Preinscripcion, Abono)."""

    __tablename__ = "tipo_cargo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    calculo: Mapped[CalculoCargo] = mapped_column(TIPO_CALCULO_CARGO, nullable=False)
    monto_fijo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_tipo_cargo_temporada"),
        UniqueConstraint("temporada_id", "nombre", name="uq_tipo_cargo_temporada_nombre"),
        # Monto si y solo si es de monto fijo.
        CheckConstraint(
            "(calculo = 'monto_fijo') = (monto_fijo IS NOT NULL)",
            name="ck_tipo_cargo_monto_segun_calculo",
        ),
    )
