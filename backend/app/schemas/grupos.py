"""Esquemas de salida de la capability grupos."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import Turno


class GrupoParaInscribir(BaseModel):
    """Un grupo donde se puede inscribir a un alumno, con la marca de
    sugerido segun la fecha de nacimiento consultada."""

    # El servicio devuelve diccionarios (las columnas de la consulta mas las dos
    # edades calculadas); model_validate los acepta y descarta la clave extra
    # `temporada_nombre`. from_attributes queda por si se valida un objeto.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    turno: Turno
    nacimiento_desde: date
    nacimiento_hasta: date
    sugerido: bool
    edad_desde: int
    edad_hasta: int
