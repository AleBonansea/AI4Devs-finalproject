"""Esquemas de salida de la capability personas."""

from pydantic import BaseModel, ConfigDict


class PersonaEncontrada(BaseModel):
    """La persona de la busqueda por DNI. Solo id, nombre y apellido: ni
    telefono, ni DNI, ni familias."""

    # from_attributes: se valida desde la fila de la consulta del servicio.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
