"""Rutas de familias. Solo traducen el resultado de app/services/familias.py
a HTTP."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import StringConstraints
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, MENSAJE_SIN_PERMISO, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.errores import respuesta_de_error
from app.schemas.familias import FamiliaEncontrada
from app.services.familias import buscar_familias_por_apellido

router = APIRouter(prefix="/familias", tags=["familias"])

# Se recorta antes de medir: " P " tiene un solo caracter y da 422.
TextoApellido = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]


@router.get(
    "",
    response_model=list[FamiliaEncontrada],
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
    },
)
def buscar_familias(
    _: Annotated[
        Usuario,
        Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR, RolUsuario.PROFESOR)),
    ],
    sesion: Annotated[Session, Depends(obtener_sesion)],
    apellido: Annotated[TextoApellido, Query()],
) -> list[FamiliaEncontrada]:
    # Sin filtro por grupo para el Profesor: lo que se limita es la respuesta.
    filas = buscar_familias_por_apellido(sesion, apellido)
    return [FamiliaEncontrada.model_validate(fila) for fila in filas]
