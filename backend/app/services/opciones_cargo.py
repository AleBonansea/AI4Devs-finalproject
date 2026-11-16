"""Opciones para registrar un cargo: tipos y períodos de la temporada vigente."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tarifario import PeriodoCobro, TipoCargo
from app.models.temporada import EstadoTemporada, Temporada
from app.schemas.cargos import OpcionesDeCargo, PeriodoOpcion, TipoDeCargoOpcion


def obtener_opciones_de_cargo(sesion: Session) -> OpcionesDeCargo:
    """Tipos por nombre y períodos por modalidad (orden del enumerado: mes,
    quincena, semana), fecha de inicio e id. Solo la temporada vigente."""
    tipos = sesion.execute(
        select(TipoCargo)
        .join(Temporada, Temporada.id == TipoCargo.temporada_id)
        .where(Temporada.estado == EstadoTemporada.VIGENTE)
        .order_by(TipoCargo.nombre, TipoCargo.id)
    ).scalars()
    periodos = sesion.execute(
        select(PeriodoCobro)
        .join(Temporada, Temporada.id == PeriodoCobro.temporada_id)
        .where(Temporada.estado == EstadoTemporada.VIGENTE)
        .order_by(PeriodoCobro.modalidad, PeriodoCobro.fecha_desde, PeriodoCobro.id)
    ).scalars()
    return OpcionesDeCargo(
        tipos_cargo=[TipoDeCargoOpcion.model_validate(t) for t in tipos],
        periodos=[PeriodoOpcion.model_validate(p) for p in periodos],
    )
