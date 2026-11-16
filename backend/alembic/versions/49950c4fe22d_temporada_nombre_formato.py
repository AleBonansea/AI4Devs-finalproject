"""temporada_nombre_formato

Revision ID: 49950c4fe22d
Revises: ff52922aeab6
Create Date: 2026-11-16 12:16:52.958665

"""

from collections.abc import Sequence

from alembic import op

revision: str = "49950c4fe22d"
down_revision: str | None = "ff52922aeab6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Escrita a mano: autogenerate no compara CHECK constraints y genero una
# migracion vacia. Si ya existiera una temporada con otro formato, el upgrade
# falla a proposito: no se corrige el dato en silencio.


def upgrade() -> None:
    op.create_check_constraint(
        "ck_temporada_nombre_formato",
        "temporada",
        "nombre ~ '^[0-9]{4}-[0-9]{2}$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_temporada_nombre_formato", "temporada", type_="check")
