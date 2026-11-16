"""La asistencia: presencia de un alumno en un dia y turno.

Cada registro cuelga de una inscripcion (alumno x grupo/turno x temporada),
que ya lleva el turno: por eso la unicidad es (inscripcion, fecha) y un mismo
alumno puede tener un registro por turno en la misma fecha. Ninguna FK borra
en cascada: nada se borra fisicamente.

No usa `MarcaDeCreacion`: `creado_en` diria cuando se tomo por primera vez, y
el modelo de datos pide quien y cuando la toco por ultima vez. Por eso
`registrado_por` y `registrado_en` se reescriben en cada correccion, con la
hora de la base. La asistencia no interviene en el cobro.
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Asistencia(Base):
    __tablename__ = "asistencia"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inscripcion_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # Sin default a proposito: quien registra tiene que decir presente o ausente.
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    registrado_por: Mapped[int] = mapped_column(BigInteger, nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["inscripcion_id"], ["inscripcion.id"], name="fk_asistencia_inscripcion"
        ),
        ForeignKeyConstraint(
            ["registrado_por"], ["usuario.id"], name="fk_asistencia_registrado_por"
        ),
        UniqueConstraint("inscripcion_id", "fecha", name="uq_asistencia_inscripcion_fecha"),
    )
