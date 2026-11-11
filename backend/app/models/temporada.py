"""La temporada: el eje del modelo.

De ella cuelga toda la configuracion del verano y todo lo que arranca de
cero cada año. Alumnos, familias, personas y usuarios NO cuelgan de la
temporada: se conservan de un año al otro.
"""

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EstadoTemporada(enum.StrEnum):
    VIGENTE = "vigente"
    CERRADA = "cerrada"


class Temporada(Base):
    __tablename__ = "temporada"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cierre: Mapped[date] = mapped_column(Date, nullable=False)
    # SQLAlchemy manda a Postgres los NOMBRES de los miembros ('VIGENTE'), no sus
    # valores ('vigente'), salvo que se le pase values_callable. Sin eso, el tipo
    # de la base queda en mayusculas mientras el modelo de datos, la API y el
    # indice parcial de abajo hablan en minusculas: el indice no agarraria nunca.
    estado: Mapped[EstadoTemporada] = mapped_column(
        Enum(
            EstadoTemporada,
            name="estado_temporada",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    # Se usa en el cierre de canon, que es posterior al lote 1.
    porcentaje_canon: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    __table_args__ = (
        CheckConstraint("fecha_inicio < fecha_cierre", name="ck_temporada_fechas"),
        CheckConstraint(
            "porcentaje_canon IS NULL OR (porcentaje_canon >= 0 AND porcentaje_canon <= 100)",
            name="ck_temporada_canon_rango",
        ),
        # Una sola temporada vigente a la vez. Es un indice unico parcial, no
        # un CHECK: la restriccion es entre filas, no dentro de una.
        Index(
            "uq_temporada_una_vigente",
            "estado",
            unique=True,
            postgresql_where=text("estado = 'vigente'"),
        ),
    )
