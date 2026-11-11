from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import obtener_configuracion


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy 2. Los modelos usan `Mapped[...]` y
    `mapped_column(...)`, no `Column(...)`."""


motor = create_engine(obtener_configuracion().database_url, pool_pre_ping=True)
FabricaDeSesiones = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion() -> Iterator[Session]:
    """Dependencia de FastAPI. Una sesion por peticion, cerrada al terminar.

    Los tests reemplazan esta dependencia por una atada a una transaccion
    que se revierte, para que cada test arranque limpio.
    """
    sesion = FabricaDeSesiones()
    try:
        yield sesion
    finally:
        sesion.close()
