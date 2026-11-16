"""El pago: lo que una familia entrego para saldar un cargo.

Puede haber varios pagos parciales por cargo. El tope (la suma de los pagos
no anulados no supera el total del cargo) mira otras filas, asi que no es un
`CHECK`: lo valida el servicio bloqueando el cargo. Ninguna FK borra en
cascada: un pago mal cargado se anula, no se borra.

Las columnas de anulacion existen desde el principio, vacias, para no migrar
cuando llegue la anulacion; toda suma de pagos filtra `anulado_en IS NULL`.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion


class Pago(MarcaDeCreacion, Base):
    __tablename__ = "pago"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cargo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Cuando pago la familia: la escribe el Admin. La usa el cierre de canon.
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    registrado_por: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Momento del registro (dato de negocio); `creado_en` es la auditoria.
    registrado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anulado_por: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    motivo_anulacion: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(["cargo_id"], ["cargo.id"], name="fk_pago_cargo"),
        ForeignKeyConstraint(["registrado_por"], ["usuario.id"], name="fk_pago_registrado_por"),
        ForeignKeyConstraint(["anulado_por"], ["usuario.id"], name="fk_pago_anulado_por"),
        CheckConstraint("monto > 0", name="ck_pago_monto_positivo"),
        # Las tres columnas de la anulacion, completas o vacias a la vez.
        CheckConstraint(
            "(anulado_en IS NULL) = (anulado_por IS NULL) "
            "AND (anulado_en IS NULL) = (motivo_anulacion IS NULL)",
            name="ck_pago_anulacion_completa",
        ),
        Index("ix_pago_cargo", "cargo_id"),
    )
