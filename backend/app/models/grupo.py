"""Grupos de la temporada y la asignacion de profesores.

El grupo es por temporada porque el rango de nacimiento se corre cada año.
Ninguna FK borra en cascada: nada se borra fisicamente, y una cascada
borraria en silencio lo que cuelga del grupo.
"""

from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import TIPO_TURNO, Turno


class Grupo(MarcaDeCreacion, Base):
    __tablename__ = "grupo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    temporada_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    turno: Mapped[Turno] = mapped_column(TIPO_TURNO, nullable=False)
    # Sugiere el grupo al cargar un alumno, no lo impone.
    nacimiento_desde: Mapped[date] = mapped_column(Date, nullable=False)
    nacimiento_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    # La baja es desactivar. server_default y no solo default: el valor lo
    # pone la base aunque la fila no entre por el ORM.
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    __table_args__ = (
        ForeignKeyConstraint(["temporada_id"], ["temporada.id"], name="fk_grupo_temporada"),
        CheckConstraint("nacimiento_desde <= nacimiento_hasta", name="ck_grupo_nacimiento"),
        UniqueConstraint("temporada_id", "nombre", "turno", name="uq_grupo_temporada_nombre_turno"),
        # Redundante como unicidad (id ya es unico), pero es la clave a la que
        # apunta la FK compuesta de `inscripcion`: asi la inscripcion no puede
        # quedar en un turno o una temporada distintos de los de su grupo.
        UniqueConstraint("id", "temporada_id", "turno", name="uq_grupo_id_temporada_turno"),
    )


class GrupoProfesor(MarcaDeCreacion, Base):
    """Asignacion N:M. Que el usuario tenga rol profesor lo valida la API:
    una FK no puede mirar el rol."""

    __tablename__ = "grupo_profesor"

    grupo_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(["grupo_id"], ["grupo.id"], name="fk_grupo_profesor_grupo"),
        ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name="fk_grupo_profesor_usuario"),
    )
