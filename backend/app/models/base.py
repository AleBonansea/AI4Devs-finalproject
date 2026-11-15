"""Piezas que comparten los modelos."""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import Mapped, mapped_column


class MarcaDeCreacion:
    """`creado_en` con la hora del servidor de base, no del proceso.

    Si la pone Python, dos procesos con relojes distintos escriben ordenes
    distintos, y en una cuenta corriente el orden de los asientos importa.
    """

    creado_en: Mapped[datetime] = mapped_column(
        # timezone=True -> timestamptz. Sin esto Postgres guarda un timestamp
        # desnudo: el servidor en UTC y el club en Argentina escriben horas que
        # no se pueden comparar, y nadie se entera hasta auditar un cobro.
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# Las vistas van sobre un MetaData PROPIO y no sobre Base.metadata: si
# estuvieran en Base.metadata, autogenerate propondria crearlas como tabla en
# cada migracion. Las crea y las borra la migracion con SQL escrito a mano.
metadata_vistas = MetaData()
