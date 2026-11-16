"""tipo_cargo monto fijo positivo

Revision ID: c4a80c343c83
Revises: a64e83ff89ab
Create Date: 2026-11-13 10:14:29.209658

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c4a80c343c83"
down_revision: str | None = "a64e83ff89ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Escrita a mano: autogenerate no compara CHECK constraints y genero una
# migracion vacia. El monto fijo NULL (tipos por tarifario) pasa el CHECK,
# porque un CHECK que da NULL no rechaza la fila.


def upgrade() -> None:
    op.create_check_constraint(
        "ck_tipo_cargo_monto_fijo_positivo",
        "tipo_cargo",
        "monto_fijo > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tipo_cargo_monto_fijo_positivo", "tipo_cargo", type_="check")
