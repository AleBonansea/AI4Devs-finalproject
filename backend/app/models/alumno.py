"""El alumno y su inscripcion en un grupo y turno de una temporada.

El alumno se conserva de una temporada a otra; la inscripcion se hace de
nuevo cada temporada. Ninguna FK borra en cascada: nada se borra
fisicamente, y una cascada borraria en silencio las inscripciones.

Las columnas medicas y de consentimiento llegan con su historia (HU-AF-06/07),
y `inscripcion.modalidad_sugerida` con HU-CC-05: una columna sin quien la
escriba es una columna que nadie prueba.
"""

from datetime import date

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import TIPO_TURNO, Turno


class Alumno(MarcaDeCreacion, Base):
    __tablename__ = "alumno"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    familia_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    # Puede ser distinto del de sus hermanos (medio hermanos).
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    # Sugiere el grupo y decide el hijo mayor de la etiqueta de la familia.
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["familia_id"], ["familia.id"], name="fk_alumno_familia"),
        # Los hijos de una familia, y la vista de la etiqueta, que agrupa por familia.
        Index("ix_alumno_familia_id", "familia_id"),
    )


# Busqueda por prefijo de apellido sin distinguir mayusculas:
# `lower(apellido) LIKE 'pe%'`. varchar_pattern_ops hace que el indice sirva
# para LIKE con prefijo aunque la base no use la intercalacion C. Va fuera de
# la clase porque necesita la columna ya mapeada; la etiqueta es solo la clave
# de postgresql_ops, no llega al SQL.
Index(
    "ix_alumno_apellido_lower",
    func.lower(Alumno.__table__.c.apellido).label("apellido_lower"),
    postgresql_ops={"apellido_lower": "varchar_pattern_ops"},
)


class Inscripcion(MarcaDeCreacion, Base):
    __tablename__ = "inscripcion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    alumno_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    grupo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Temporada y turno se copian del grupo para poder declarar la unicidad;
    # la FK compuesta garantiza que coincidan con los del grupo.
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    turno: Mapped[Turno] = mapped_column(TIPO_TURNO, nullable=False)
    creado_por: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["alumno_id"], ["alumno.id"], name="fk_inscripcion_alumno"),
        # Apunta a uq_grupo_id_temporada_turno de grupo.
        ForeignKeyConstraint(
            ["grupo_id", "temporada_id", "turno"],
            ["grupo.id", "grupo.temporada_id", "grupo.turno"],
            name="fk_inscripcion_grupo",
        ),
        ForeignKeyConstraint(["creado_por"], ["usuario.id"], name="fk_inscripcion_creado_por"),
        # A lo sumo un grupo por turno y temporada; puede estar en los dos turnos.
        UniqueConstraint(
            "alumno_id", "temporada_id", "turno", name="uq_inscripcion_alumno_temporada_turno"
        ),
        Index("ix_inscripcion_grupo_id", "grupo_id"),
    )
