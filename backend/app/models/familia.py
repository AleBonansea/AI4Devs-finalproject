"""Familias, personas y el vinculo entre ellas.

La familia NO es por temporada: se conserva de un año al otro, con su
categoria y sus personas. Ninguna FK borra en cascada: nada se borra
fisicamente, y una cascada borraria en silencio los vinculos de una persona.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion
from app.models.enums import TIPO_CATEGORIA_FAMILIA, CategoriaFamilia


class Familia(MarcaDeCreacion, Base):
    __tablename__ = "familia"

    # El id nunca cambia: la etiqueta visible se recalcula, el id no.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    categoria: Mapped[CategoriaFamilia] = mapped_column(TIPO_CATEGORIA_FAMILIA, nullable=False)


class Persona(MarcaDeCreacion, Base):
    """Un adulto que se guarda una sola vez y se reutiliza entre familias."""

    __tablename__ = "persona"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    # NOT NULL: la persona existe en el sistema para poder ser llamada.
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    # NULL: ninguna fuente lo exige. El UNIQUE admite varios nulos en Postgres.
    dni: Mapped[str | None] = mapped_column(String(15), nullable=True)

    __table_args__ = (
        # Nombre explicito: el servicio del alta reconoce por este nombre el
        # choque de DNI en el IntegrityError (carrera entre dos altas).
        UniqueConstraint("dni", name="uq_persona_dni"),
    )


class FamiliaPersona(MarcaDeCreacion, Base):
    """Vinculo N:M con las marcas del rol de la persona en esa familia."""

    __tablename__ = "familia_persona"

    familia_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    persona_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # server_default ademas de default: el valor lo pone la base aunque la
    # fila no entre por el ORM.
    es_tutor: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    autorizado_retiro: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    contacto_emergencia: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    __table_args__ = (
        ForeignKeyConstraint(["familia_id"], ["familia.id"], name="fk_familia_persona_familia"),
        ForeignKeyConstraint(["persona_id"], ["persona.id"], name="fk_familia_persona_persona"),
        # Un tutor siempre esta autorizado a retirar.
        CheckConstraint(
            "NOT es_tutor OR autorizado_retiro", name="ck_familia_persona_tutor_retira"
        ),
        # Un vinculo sin ninguna marca no dice nada.
        CheckConstraint(
            "es_tutor OR autorizado_retiro OR contacto_emergencia",
            name="ck_familia_persona_alguna_marca",
        ),
        # La PK ya cubre las busquedas por familia_id (va primero); este
        # cubre "en que familias esta esta persona".
        Index("ix_familia_persona_persona_id", "persona_id"),
    )


# La vista de la etiqueta "Apellido – Hijo mayor". Va sobre un MetaData
# PROPIO y no sobre Base.metadata: si estuviera en Base.metadata, autogenerate
# propondria crearla como tabla en cada migracion. La crea y la borra la
# migracion con SQL escrito a mano.
metadata_vistas = MetaData()

v_familia_etiqueta = Table(
    "v_familia_etiqueta",
    metadata_vistas,
    Column("familia_id", BigInteger, primary_key=True),
    Column("etiqueta", String),
)
