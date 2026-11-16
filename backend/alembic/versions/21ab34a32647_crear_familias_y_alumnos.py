"""crear familias y alumnos

Revision ID: 21ab34a32647
Revises: c4a80c343c83
Create Date: 2026-11-13 16:03:28.374583

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "21ab34a32647"
down_revision: str | None = "c4a80c343c83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Corregido a mano. Autogenerate escribe `sa.Enum(..., name="turno")`, que
# intentaria crear el tipo. `turno` y `categoria_familia` ya existen: los creo
# a64e83ff89ab, que tambien los borra en su downgrade. Aca se referencian con
# create_type=False y este downgrade no los toca: los siguen usando `grupo` y
# los descuentos.
TURNO = postgresql.ENUM("manana", "tarde", name="turno", create_type=False)
CATEGORIA_FAMILIA = postgresql.ENUM(
    "socio", "empleado", "no_socio", name="categoria_familia", create_type=False
)

# Agregado a mano: autogenerate no ve la vista (esta sobre un MetaData propio,
# ver app/models/familia.py). La raya es U+2013 entre espacios. El desempate
# por id es el "se registro primero" de los mellizos.
CREAR_VISTA_ETIQUETA = """
CREATE VIEW v_familia_etiqueta AS
SELECT DISTINCT ON (familia_id)
    familia_id,
    apellido || ' – ' || nombre AS etiqueta
FROM alumno
ORDER BY familia_id, fecha_nacimiento, id
"""


def upgrade() -> None:
    op.create_table(
        "familia",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("categoria", CATEGORIA_FAMILIA, nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "persona",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("apellido", sa.String(length=80), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("dni", sa.String(length=15), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dni", name="uq_persona_dni"),
    )
    op.create_table(
        "alumno",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("familia_id", sa.BigInteger(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("apellido", sa.String(length=80), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["familia_id"], ["familia.id"], name="fk_alumno_familia"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alumno_familia_id", "alumno", ["familia_id"], unique=False)
    # Corregido a mano: autogenerate escribio `sa.text("lower(apellido)")` con
    # un postgresql_ops por etiqueta que no se aplica a una expresion de texto,
    # y el indice quedaba sin varchar_pattern_ops (no sirve para LIKE 'pe%').
    op.create_index(
        "ix_alumno_apellido_lower",
        "alumno",
        [sa.text("lower(apellido) varchar_pattern_ops")],
        unique=False,
    )
    op.create_table(
        "familia_persona",
        sa.Column("familia_id", sa.BigInteger(), nullable=False),
        sa.Column("persona_id", sa.BigInteger(), nullable=False),
        sa.Column("es_tutor", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "autorizado_retiro", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "contacto_emergencia", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "NOT es_tutor OR autorizado_retiro", name="ck_familia_persona_tutor_retira"
        ),
        sa.CheckConstraint(
            "es_tutor OR autorizado_retiro OR contacto_emergencia",
            name="ck_familia_persona_alguna_marca",
        ),
        sa.ForeignKeyConstraint(["familia_id"], ["familia.id"], name="fk_familia_persona_familia"),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.id"], name="fk_familia_persona_persona"),
        sa.PrimaryKeyConstraint("familia_id", "persona_id"),
    )
    op.create_index(
        "ix_familia_persona_persona_id", "familia_persona", ["persona_id"], unique=False
    )
    op.create_table(
        "inscripcion",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("alumno_id", sa.BigInteger(), nullable=False),
        sa.Column("grupo_id", sa.BigInteger(), nullable=False),
        sa.Column("temporada_id", sa.BigInteger(), nullable=False),
        sa.Column("turno", TURNO, nullable=False),
        sa.Column("creado_por", sa.BigInteger(), nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["alumno_id"], ["alumno.id"], name="fk_inscripcion_alumno"),
        sa.ForeignKeyConstraint(
            ["grupo_id", "temporada_id", "turno"],
            ["grupo.id", "grupo.temporada_id", "grupo.turno"],
            name="fk_inscripcion_grupo",
        ),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"], name="fk_inscripcion_creado_por"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alumno_id", "temporada_id", "turno", name="uq_inscripcion_alumno_temporada_turno"
        ),
    )
    op.create_index("ix_inscripcion_grupo_id", "inscripcion", ["grupo_id"], unique=False)

    op.execute(CREAR_VISTA_ETIQUETA)


def downgrade() -> None:
    # La vista primero: depende de `alumno` y bloquearia su DROP TABLE.
    op.execute("DROP VIEW v_familia_etiqueta")

    # Orden inverso a las FK.
    op.drop_index("ix_inscripcion_grupo_id", table_name="inscripcion")
    op.drop_table("inscripcion")
    op.drop_index("ix_familia_persona_persona_id", table_name="familia_persona")
    op.drop_table("familia_persona")
    op.drop_index("ix_alumno_apellido_lower", table_name="alumno")
    op.drop_index("ix_alumno_familia_id", table_name="alumno")
    op.drop_table("alumno")
    op.drop_table("persona")
    op.drop_table("familia")
    # Los tipos `turno` y `categoria_familia` NO se borran: son de a64e83ff89ab.
