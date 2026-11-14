"""Esquemas de la capability asistencia. Declaran solo los campos que la
pantalla necesita: es lo que impide que se cuele otro dato del alumno."""

from datetime import date

from pydantic import BaseModel

from app.models.enums import Turno


class AlumnoEnAsistencia(BaseModel):
    inscripcion_id: int
    nombre: str
    apellido: str
    # None: todavia no se tomo asistencia a este alumno en esa fecha.
    presente: bool | None


class AsistenciaDelGrupo(BaseModel):
    grupo_id: int
    grupo: str
    turno: Turno
    fecha: date
    alumnos: list[AlumnoEnAsistencia]
