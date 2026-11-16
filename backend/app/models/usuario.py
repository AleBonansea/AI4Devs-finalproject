"""Cada persona del staff que ingresa al sistema.

El Profesor es un usuario con rol `profesor`: no hay tabla de profesores
aparte. Los usuarios no son por temporada.
"""

import enum

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Enum, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import MarcaDeCreacion


class RolUsuario(enum.StrEnum):
    ADMIN = "admin"
    COORDINADOR = "coordinador"
    PROFESOR = "profesor"


class Usuario(MarcaDeCreacion, Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)

    # Hash argon2. La contrasena en texto no se guarda ni se registra nunca.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Para impedir que al cambiarla se repita la anterior (HU-UT-06).
    password_hash_anterior: Mapped[str | None] = mapped_column(String(255), nullable=True)
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # El bloqueo NO tiene columna propia: se deduce de este contador
    # (>= 5 esta bloqueado). Dos datos que digan lo mismo se desincronizan.
    intentos_fallidos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(
            RolUsuario,
            name="rol_usuario",
            native_enum=True,
            validate_strings=True,
            # Ver la nota en temporada.py: sin esto el tipo queda en mayusculas.
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    # La baja es desactivar: el usuario se conserva para no romper las
    # referencias de quien cobro, anulo o abono.
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("intentos_fallidos >= 0", name="ck_usuario_intentos_no_negativos"),
    )

    @property
    def bloqueado(self) -> bool:
        return self.intentos_fallidos >= 5
