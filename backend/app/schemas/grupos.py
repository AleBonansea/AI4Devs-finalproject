"""Esquemas de salida de la capability grupos."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import Turno


class GrupoParaInscribir(BaseModel):
    """Un grupo donde se puede inscribir a un alumno, con la marca de
    sugerido segun la fecha de nacimiento consultada."""

    # from_attributes: se valida desde las filas de la consulta del servicio.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    turno: Turno
    nacimiento_desde: date
    nacimiento_hasta: date
    sugerido: bool
