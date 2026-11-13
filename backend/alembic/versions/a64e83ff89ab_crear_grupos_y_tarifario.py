"""crear grupos y tarifario

Revision ID: a64e83ff89ab
Revises: 17e635c64a3e
Create Date: 2026-11-13 09:49:06.150497

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a64e83ff89ab"
down_revision: str | None = "17e635c64a3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Corregido a mano. Autogenerate escribe un `sa.Enum(..., name="turno")` en
# cada columna y deja que cada `create_table` cree el tipo de forma implicita
# (SQLAlchemy comprueba si ya existe, asi que no revienta, pero el CREATE TYPE
# queda escondido). Aca los cuatro tipos se crean una sola vez, a la vista y
# sin checkfirst -si ya existieran, es un error que tiene que saltar-, y las
# columnas los usan con create_type=False. El downgrade los borra en espejo.
TURNO = postgresql.ENUM("manana", "tarde", name="turno", create_type=False)
MODALIDAD = postgresql.ENUM("mes", "quincena", "semana", "dia", name="modalidad", create_type=False)
CATEGORIA_FAMILIA = postgresql.ENUM(
    "socio", "empleado", "no_socio", name="categoria_familia", create_type=False
)
CALCULO_CARGO = postgresql.ENUM("monto_fijo", "tarifario", name="calculo_cargo", create_type=False)
TIPOS = (TURNO, MODALIDAD, CATEGORIA_FAMILIA, CALCULO_CARGO)


def upgrade() -> None:
    for tipo in TIPOS:
        tipo.create(op.get_bind(), checkfirst=False)

    # Reordenado a mano: autogenerate las saca por orden alfabetico.
    op.create_table(
        "grupo",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("nombre", sa.String(length=60), nullable=False),
        sa.Column("turno", TURNO, nullable=False),
        sa.Column("nacimiento_desde", sa.Date(), nullable=False),
        sa.Column("nacimiento_hasta", sa.Date(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("nacimiento_desde <= nacimiento_hasta", name="ck_grupo_nacimiento"),
        sa.ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_grupo_temporada"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "temporada_id", "turno", name="uq_grupo_id_temporada_turno"),
        sa.UniqueConstraint(
            "temporada_id", "nombre", "turno", name="uq_grupo_temporada_nombre_turno"
        ),
    )
    op.create_table(
        "grupo_profesor",
        sa.Column("grupo_id", sa.BigInteger(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["grupo_id"], ["grupo.id"], name="fk_grupo_profesor_grupo"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name="fk_grupo_profesor_usuario"),
        sa.PrimaryKeyConstraint("grupo_id", "usuario_id"),
    )
    op.create_table(
        "tarifa_base",
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("turno", TURNO, nullable=False),
        sa.Column("modalidad", MODALIDAD, nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("monto > 0", name="ck_tarifa_base_monto_positivo"),
        sa.ForeignKeyConstraint(
            ["temporada_id"], ["temporada.id"], name="fk_tarifa_base_temporada"
        ),
        sa.PrimaryKeyConstraint("temporada_id", "turno", "modalidad"),
    )
    op.create_table(
        "descuento_modalidad",
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria", CATEGORIA_FAMILIA, nullable=False),
        sa.Column("modalidad", MODALIDAD, nullable=False),
        sa.Column("porcentaje", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("modalidad <> 'mes'", name="ck_descuento_modalidad_no_mes"),
        sa.CheckConstraint(
            "porcentaje BETWEEN 0 AND 100", name="ck_descuento_modalidad_porcentaje_rango"
        ),
        sa.ForeignKeyConstraint(
            ["temporada_id"], ["temporada.id"], name="fk_descuento_modalidad_temporada"
        ),
        sa.PrimaryKeyConstraint("temporada_id", "categoria", "modalidad"),
    )
    op.create_table(
        "descuento_mes",
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria", CATEGORIA_FAMILIA, nullable=False),
        sa.Column("tramo_hijos", sa.SmallInteger(), nullable=False),
        sa.Column("porcentaje", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "porcentaje BETWEEN 0 AND 100", name="ck_descuento_mes_porcentaje_rango"
        ),
        sa.CheckConstraint("tramo_hijos BETWEEN 1 AND 4", name="ck_descuento_mes_tramo_rango"),
        sa.ForeignKeyConstraint(
            ["temporada_id"], ["temporada.id"], name="fk_descuento_mes_temporada"
        ),
        sa.PrimaryKeyConstraint("temporada_id", "categoria", "tramo_hijos"),
    )
    op.create_table(
        "periodo_cobro",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("modalidad", MODALIDAD, nullable=False),
        sa.Column("nombre", sa.String(length=40), nullable=False),
        sa.Column("fecha_desde", sa.Date(), nullable=False),
        sa.Column("fecha_hasta", sa.Date(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("modalidad <> 'dia'", name="ck_periodo_cobro_no_dia"),
        sa.CheckConstraint("fecha_desde <= fecha_hasta", name="ck_periodo_cobro_fechas"),
        sa.ForeignKeyConstraint(
            ["temporada_id"], ["temporada.id"], name="fk_periodo_cobro_temporada"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "modalidad", name="uq_periodo_cobro_id_modalidad"),
        sa.UniqueConstraint(
            "temporada_id",
            "modalidad",
            "nombre",
            name="uq_periodo_cobro_temporada_modalidad_nombre",
        ),
    )
    op.create_table(
        "tipo_cargo",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("nombre", sa.String(length=60), nullable=False),
        sa.Column("calculo", CALCULO_CARGO, nullable=False),
        sa.Column("monto_fijo", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "(calculo = 'monto_fijo') = (monto_fijo IS NOT NULL)",
            name="ck_tipo_cargo_monto_segun_calculo",
        ),
        sa.ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_tipo_cargo_temporada"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("temporada_id", "nombre", name="uq_tipo_cargo_temporada_nombre"),
    )


def downgrade() -> None:
    # Orden inverso al upgrade: grupo_profesor antes que grupo.
    op.drop_table("tipo_cargo")
    op.drop_table("periodo_cobro")
    op.drop_table("descuento_mes")
    op.drop_table("descuento_modalidad")
    op.drop_table("tarifa_base")
    op.drop_table("grupo_profesor")
    op.drop_table("grupo")

    # Agregado a mano: drop_table no borra los tipos enumerados, y sin esto el
    # upgrade siguiente falla con 'type "turno" already exists'.
    sa.Enum(name="calculo_cargo").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="categoria_familia").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="modalidad").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="turno").drop(op.get_bind(), checkfirst=True)
