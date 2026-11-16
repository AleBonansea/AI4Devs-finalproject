"""El cargo: lo que una familia tiene que pagar por un alumno.

Guarda el resultado del calculo (categoria, hijos, base, % y total), no solo
la referencia al tarifario: el tarifario cambia y lo ya cobrado no se
recalcula. Las reglas de forma viven en `CHECK` porque son de una sola fila;
la coherencia con otras tablas (alumno de la familia, inscripcion de la
temporada, tipo de cargo) la valida el servicio, que es el unico que escribe
cargos. Ninguna FK borra en cascada.

Los tres indices unicos son parciales y existen para que el doble clic (dos
pedidos simultaneos) no duplique un cargo: un `SELECT` previo no lo garantiza.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    Numeric,
    SmallInteger,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import (
    TIPO_CATEGORIA_FAMILIA,
    TIPO_MODALIDAD,
    CategoriaFamilia,
    Modalidad,
)


class Cargo(MarcaDeCreacion, Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Se copia del alumno al crear el cargo: la cuenta corriente es de la familia.
    familia_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alumno_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo_cargo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Solo en el Abono: da el turno.
    inscripcion_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Solo en el Abono. NULL es un cargo de monto fijo.
    modalidad: Mapped[Modalidad | None] = mapped_column(TIPO_MODALIDAD, nullable=True)
    periodo_cobro_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Solo para la modalidad Dia.
    fecha_dia: Mapped[date | None] = mapped_column(Date, nullable=True)
    categoria_aplicada: Mapped[CategoriaFamilia] = mapped_column(
        TIPO_CATEGORIA_FAMILIA, nullable=False
    )
    # Solo en el Mes: hijos inscriptos en ese turno al momento del calculo.
    cantidad_hijos_aplicada: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    porcentaje_aplicado: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    creado_por: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_cargo_temporada"),
        ForeignKeyConstraint(["familia_id"], ["familia.id"], name="fk_cargo_familia"),
        ForeignKeyConstraint(["alumno_id"], ["alumno.id"], name="fk_cargo_alumno"),
        ForeignKeyConstraint(["tipo_cargo_id"], ["tipo_cargo.id"], name="fk_cargo_tipo_cargo"),
        ForeignKeyConstraint(["inscripcion_id"], ["inscripcion.id"], name="fk_cargo_inscripcion"),
        ForeignKeyConstraint(["creado_por"], ["usuario.id"], name="fk_cargo_creado_por"),
        # El periodo es de la modalidad del cargo. La FK compuesta es MATCH
        # SIMPLE: con modalidad NULL no comprueba nada, por eso existe
        # `ck_cargo_monto_fijo_sin_abono`.
        ForeignKeyConstraint(
            ["periodo_cobro_id", "modalidad"],
            ["periodo_cobro.id", "periodo_cobro.modalidad"],
            name="fk_cargo_periodo_cobro",
        ),
        CheckConstraint(
            "modalidad IS NOT NULL OR (inscripcion_id IS NULL AND periodo_cobro_id IS NULL "
            "AND fecha_dia IS NULL AND cantidad_hijos_aplicada IS NULL)",
            name="ck_cargo_monto_fijo_sin_abono",
        ),
        CheckConstraint(
            "modalidad IS NULL OR inscripcion_id IS NOT NULL",
            name="ck_cargo_abono_con_inscripcion",
        ),
        # Dia: fecha y sin periodo. Mes, Quincena, Semana: periodo y sin fecha.
        CheckConstraint(
            "modalidad IS NULL "
            "OR (modalidad = 'dia' AND fecha_dia IS NOT NULL AND periodo_cobro_id IS NULL) "
            "OR (modalidad <> 'dia' AND periodo_cobro_id IS NOT NULL AND fecha_dia IS NULL)",
            name="ck_cargo_periodo_o_fecha",
        ),
        # IS NOT DISTINCT FROM: con `=` a secas, una modalidad NULL daria NULL
        # y el CHECK pasaria.
        CheckConstraint(
            "(modalidad IS NOT DISTINCT FROM 'mes') = (cantidad_hijos_aplicada IS NOT NULL)",
            name="ck_cargo_hijos_solo_mes",
        ),
        CheckConstraint("cantidad_hijos_aplicada >= 1", name="ck_cargo_hijos_positivo"),
        CheckConstraint("monto_base > 0", name="ck_cargo_monto_base_positivo"),
        CheckConstraint("porcentaje_aplicado BETWEEN 0 AND 100", name="ck_cargo_porcentaje_rango"),
        CheckConstraint(
            "monto_total = round(monto_base * (1 - porcentaje_aplicado / 100), 2)",
            name="ck_cargo_total",
        ),
        Index(
            "uq_cargo_inscripcion_periodo",
            "inscripcion_id",
            "periodo_cobro_id",
            unique=True,
            postgresql_where=text("periodo_cobro_id IS NOT NULL"),
        ),
        Index(
            "uq_cargo_inscripcion_fecha",
            "inscripcion_id",
            "fecha_dia",
            unique=True,
            postgresql_where=text("fecha_dia IS NOT NULL"),
        ),
        # El tipo es de una temporada: uno por alumno, tipo y temporada.
        Index(
            "uq_cargo_alumno_tipo_monto_fijo",
            "alumno_id",
            "tipo_cargo_id",
            unique=True,
            postgresql_where=text("modalidad IS NULL"),
        ),
        Index("ix_cargo_familia_temporada", "familia_id", "temporada_id"),
    )
