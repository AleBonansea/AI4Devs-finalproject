"""Modelos de SQLAlchemy.

Importalos todos aca: Alembic descubre las tablas por `Base.metadata`, y un
modelo que no se importa no existe para `--autogenerate`. Si falta uno, el
autogenerate propone borrar su tabla.
"""

from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import RolUsuario, Usuario

__all__ = ["EstadoTemporada", "RolUsuario", "Temporada", "Usuario"]
