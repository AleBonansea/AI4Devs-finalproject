"""El movimiento de tesoreria: un ingreso o un egreso de la temporada.

Nunca se modifica ni se borra: anular un pago agrega un egreso por el mismo
monto. `monto` es siempre positivo; el signo lo da `tipo`. Ninguna FK borra
en cascada.
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
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import (
    TIPO_ORIGEN_MOVIMIENTO,
    TIPO_TIPO_MOVIMIENTO,
    OrigenMovimiento,
    TipoMovimiento,
)


class TesoreriaMovimiento(MarcaDeCreacion, Base):
    __tablename__ = "tesoreria_movimiento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[TipoMovimiento] = mapped_column(TIPO_TIPO_MOVIMIENTO, nullable=False)
    origen: Mapped[OrigenMovimiento] = mapped_column(TIPO_ORIGEN_MOVIMIENTO, nullable=False)
    # Para los origenes `pago` y `anulacion_pago`.
    pago_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Obligatoria solo en los egresos manuales.
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    registrado_por: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_movimiento_temporada"),
        ForeignKeyConstraint(["pago_id"], ["pago.id"], name="fk_movimiento_pago"),
        ForeignKeyConstraint(
            ["registrado_por"], ["usuario.id"], name="fk_movimiento_registrado_por"
        ),
        CheckConstraint("monto > 0", name="ck_movimiento_monto_positivo"),
        # Sin la rama de `canon`: el valor existe en el enumerado, pero no hay
        # `cierre_canon` ni `cierre_canon_id` a que referenciar. La migracion
        # que cree `cierre_canon` agrega la columna y reemplaza este CHECK por
        # el de cuatro ramas. Hasta entonces un movimiento de canon se rechaza.
        CheckConstraint(
            "(origen = 'pago' AND tipo = 'ingreso' AND pago_id IS NOT NULL) "
            "OR (origen = 'anulacion_pago' AND tipo = 'egreso' AND pago_id IS NOT NULL) "
            "OR (origen = 'manual' AND tipo = 'egreso' AND descripcion IS NOT NULL "
            "AND pago_id IS NULL)",
            name="ck_movimiento_origen",
        ),
        # Con pago_id NULL (los manuales) no choca.
        UniqueConstraint("pago_id", "origen", name="uq_movimiento_pago_origen"),
        Index("ix_movimiento_temporada", "temporada_id"),
    )
