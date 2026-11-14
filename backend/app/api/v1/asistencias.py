"""Rutas de asistencia. Solo traducen el resultado de
app/services/asistencias.py a HTTP."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_GRUPO_NO_ASIGNADO, MENSAJE_SESION_INVALIDA, grupo_asignado
from app.models.usuario import Usuario
from app.schemas.asistencias import AsistenciaDelGrupo
from app.schemas.errores import respuesta_de_error
from app.services.asistencias import (
    MENSAJE_GRUPO_INEXISTENTE,
    FechaFueraDeTemporada,
    GrupoInexistente,
    abrir_asistencia,
)

router = APIRouter(prefix="/grupos/{grupo_id}/asistencias", tags=["asistencias"])


@router.get(
    "/{fecha}",
    response_model=AsistenciaDelGrupo,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_GRUPO_NO_ASIGNADO),
        status.HTTP_404_NOT_FOUND: respuesta_de_error(MENSAJE_GRUPO_INEXISTENTE),
        status.HTTP_422_UNPROCESSABLE_ENTITY: respuesta_de_error(
            "La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027."
        ),
    },
)
def abrir(
    grupo_id: int,
    fecha: date,
    _usuario: Annotated[Usuario, Depends(grupo_asignado)],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> AsistenciaDelGrupo:
    try:
        return abrir_asistencia(sesion, grupo_id, fecha)
    except GrupoInexistente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_GRUPO_INEXISTENTE
        ) from None
    except FechaFueraDeTemporada as fuera:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=fuera.mensaje
        ) from None
