"""crear_pago_y_tesoreria

Revision ID: ff52922aeab6
Revises: fd608f611c8d
Create Date: 2026-11-14 17:52:33.497909

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "ff52922aeab6"
down_revision: str | None = "fd608f611c8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Los dos enumerados nacen con `op.create_table` (que los crea una sola vez)
# y se borran a mano en el downgrade: autogenerate no escribe el DROP TYPE.
# `origen_movimiento` trae `canon` aunque el CHECK todavia no lo admita:
# agregar un valor despues no se puede revertir.
TIPO_MOVIMIENTO = postgresql.ENUM("ingreso", "egreso", name="tipo_movimiento", create_type=False)
ORIGEN_MOVIMIENTO = postgresql.ENUM(
    "pago", "anulacion_pago", "canon", "manual", name="origen_movimiento", create_type=False
)

# Pagos agregados por cargo ANTES del JOIN: un JOIN directo repetiria el
# monto_total de un cargo por cada pago, y un cargo con dos pagos contaria doble.
VISTA_CUENTA_CORRIENTE = """
CREATE VIEW v_cuenta_corriente AS
SELECT c.familia_id, c.temporada_id,
       sum(c.monto_total)                    AS total_cargos,
       coalesce(sum(p.pagado), 0)            AS total_pagos,
       sum(c.monto_total) - coalesce(sum(p.pagado), 0) AS saldo_pendiente
FROM cargo c
LEFT JOIN (SELECT cargo_id, sum(monto) AS pagado
           FROM pago WHERE anulado_en IS NULL GROUP BY cargo_id) p
       ON p.cargo_id = c.id
GROUP BY c.familia_id, c.temporada_id
"""


def upgrade() -> None:
    TIPO_MOVIMIENTO.create(op.get_bind(), checkfirst=False)
    ORIGEN_MOVIMIENTO.create(op.get_bind(), checkfirst=False)

    op.create_table(
        "pago",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("cargo_id", sa.BigInteger(), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fecha_pago", sa.Date(), nullable=False),
        sa.Column("registrado_por", sa.BigInteger(), nullable=False),
        sa.Column(
            "registrado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("anulado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anulado_por", sa.BigInteger(), nullable=True),
        sa.Column("motivo_anulacion", sa.Text(), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "(anulado_en IS NULL) = (anulado_por IS NULL) "
            "AND (anulado_en IS NULL) = (motivo_anulacion IS NULL)",
            name="ck_pago_anulacion_completa",
        ),
        sa.CheckConstraint("monto > 0", name="ck_pago_monto_positivo"),
        sa.ForeignKeyConstraint(["anulado_por"], ["usuario.id"], name="fk_pago_anulado_por"),
        sa.ForeignKeyConstraint(["cargo_id"], ["cargo.id"], name="fk_pago_cargo"),
        sa.ForeignKeyConstraint(["registrado_por"], ["usuario.id"], name="fk_pago_registrado_por"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pago_cargo", "pago", ["cargo_id"], unique=False)

    op.create_table(
        "tesoreria_movimiento",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("tipo", TIPO_MOVIMIENTO, nullable=False),
        sa.Column("origen", ORIGEN_MOVIMIENTO, nullable=False),
        sa.Column("pago_id", sa.BigInteger(), nullable=True),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("registrado_por", sa.BigInteger(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("monto > 0", name="ck_movimiento_monto_positivo"),
        sa.CheckConstraint(
            "(origen = 'pago' AND tipo = 'ingreso' AND pago_id IS NOT NULL) "
            "OR (origen = 'anulacion_pago' AND tipo = 'egreso' AND pago_id IS NOT NULL) "
            "OR (origen = 'manual' AND tipo = 'egreso' AND descripcion IS NOT NULL "
            "AND pago_id IS NULL)",
            name="ck_movimiento_origen",
        ),
        sa.ForeignKeyConstraint(["pago_id"], ["pago.id"], name="fk_movimiento_pago"),
        sa.ForeignKeyConstraint(
            ["registrado_por"], ["usuario.id"], name="fk_movimiento_registrado_por"
        ),
        sa.ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_movimiento_temporada"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pago_id", "origen", name="uq_movimiento_pago_origen"),
    )
    op.create_index(
        "ix_movimiento_temporada", "tesoreria_movimiento", ["temporada_id"], unique=False
    )

    # Escrita a mano: autogenerate no ve las vistas.
    op.execute(VISTA_CUENTA_CORRIENTE)


def downgrade() -> None:
    # En orden inverso: la vista depende de `pago`, y los tipos de las tablas.
    op.execute("DROP VIEW v_cuenta_corriente")
    op.drop_index("ix_movimiento_temporada", table_name="tesoreria_movimiento")
    op.drop_table("tesoreria_movimiento")
    op.drop_index("ix_pago_cargo", table_name="pago")
    op.drop_table("pago")
    ORIGEN_MOVIMIENTO.drop(op.get_bind(), checkfirst=False)
    TIPO_MOVIMIENTO.drop(op.get_bind(), checkfirst=False)
