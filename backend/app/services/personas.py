"""Personas: normalizacion del DNI y busqueda por DNI."""

from typing import Any

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models.familia import Persona


def normalizar_dni(texto: str) -> str:
    """Quita espacios, puntos y guiones y pasa a mayusculas.

    Unico lugar de la normalizacion: la usan el parametro de la busqueda y el
    alta, y el DNI se guarda ya normalizado.
    """
    return "".join(c for c in texto if not c.isspace() and c not in ".-").upper()


def buscar_persona_por_dni(sesion: Session, dni: str) -> Row[Any] | None:
    """La persona con ese DNI exacto (ya normalizado), o None."""
    consulta = select(Persona.id, Persona.nombre, Persona.apellido).where(Persona.dni == dni)
    return sesion.execute(consulta).one_or_none()
