"""Modelos de SQLAlchemy.

Importalos todos aca: Alembic descubre las tablas por `Base.metadata`, y un
modelo que no se importa no existe para `--autogenerate`. Si falta uno, el
autogenerate propone borrar su tabla.
"""

from app.models.alumno import Alumno, Inscripcion
from app.models.asistencia import Asistencia
from app.models.cargo import Cargo
from app.models.enums import CalculoCargo, CategoriaFamilia, Modalidad, Turno
from app.models.familia import Familia, FamiliaPersona, Persona
from app.models.grupo import Grupo, GrupoProfesor
from app.models.tarifario import (
    DescuentoMes,
    DescuentoModalidad,
    PeriodoCobro,
    TarifaBase,
    TipoCargo,
)
from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import RolUsuario, Usuario

__all__ = [
    "Asistencia",
    "Alumno",
    "CalculoCargo",
    "Cargo",
    "CategoriaFamilia",
    "DescuentoMes",
    "DescuentoModalidad",
    "EstadoTemporada",
    "Familia",
    "FamiliaPersona",
    "Grupo",
    "GrupoProfesor",
    "Inscripcion",
    "Modalidad",
    "PeriodoCobro",
    "Persona",
    "RolUsuario",
    "TarifaBase",
    "Temporada",
    "TipoCargo",
    "Turno",
    "Usuario",
]
