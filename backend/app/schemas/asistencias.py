"""Esquemas de la capability asistencia. Declaran solo los campos que la
pantalla necesita: es lo que impide que se cuele otro dato del alumno."""

from datetime import date

from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

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


class AsistenciaMarcada(BaseModel):
    inscripcion_id: int
    presente: bool


class AsistenciaEntrada(BaseModel):
    """Lo que se guarda: solo quien y si estuvo. Fecha y grupo vienen del path
    y el autor de la sesion; nada de eso se acepta del cuerpo.

    Sin tope de largo: el limite natural es el tamano del grupo, y los ids de
    otro grupo ya se rechazan por elemento.
    """

    asistencias: list[AsistenciaMarcada]

    @field_validator("asistencias")
    @classmethod
    def _no_vacia(cls, valor: list[AsistenciaMarcada]) -> list[AsistenciaMarcada]:
        if not valor:
            raise PydanticCustomError("regla_de_negocio", "Tiene que haber al menos un alumno.")
        return valor
