"""Rutas de grupos. Solo traducen el resultado de app/services/grupos.py a
HTTP."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, MENSAJE_SIN_PERMISO, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.errores import respuesta_de_error
from app.schemas.grupos import GrupoParaInscribir
from app.services.grupos import listar_grupos_para_inscribir

router = APIRouter(prefix="/grupos", tags=["grupos"])


@router.get(
    "",
    response_model=list[GrupoParaInscribir],
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
    },
)
def listar_grupos(
    usuario: Annotated[
        Usuario,
        Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR, RolUsuario.PROFESOR)),
    ],
    sesion: Annotated[Session, Depends(obtener_sesion)],
    fecha_nacimiento: date | None = None,
) -> list[GrupoParaInscribir]:
    # El Profesor recibe solo sus grupos: lo filtra la consulta del servicio.
    filas = listar_grupos_para_inscribir(sesion, usuario, fecha_nacimiento)
    return [GrupoParaInscribir.model_validate(fila) for fila in filas]
