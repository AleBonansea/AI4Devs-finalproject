"""Esquemas de salida de la capability familias."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import CategoriaFamilia, Turno


class InscripcionDeFamilia(BaseModel):
    """Una inscripción de un hijo de la familia en la temporada vigente. Solo
    estos seis campos: ningún dato médico ni de personas."""

    model_config = ConfigDict(from_attributes=True)

    inscripcion_id: int
    alumno_id: int
    nombre: str
    apellido: str
    turno: Turno
    grupo: str


class FamiliaEncontrada(BaseModel):
    """Una familia de la busqueda por apellido. Solo id, etiqueta y categoria:
    la busqueda no filtra por grupo para el Profesor, asi que lo que se limita
    es lo que trae (ni alumnos, ni fechas, ni grupos, ni personas)."""

    # from_attributes: se valida desde las filas de la consulta del servicio.
    model_config = ConfigDict(from_attributes=True)

    id: int
    etiqueta: str
    categoria: CategoriaFamilia
