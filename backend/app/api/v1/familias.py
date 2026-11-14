"""Rutas de familias. Solo traducen el resultado de app/services/familias.py
a HTTP."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AfterValidator, StringConstraints
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, MENSAJE_SIN_PERMISO, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.errores import respuesta_de_error
from app.schemas.familias import FamiliaEncontrada, InscripcionDeFamilia
from app.schemas.validadores import sin_caracteres_de_control
from app.services.familias import (
    MENSAJE_FAMILIA_INEXISTENTE,
    FamiliaInexistente,
    buscar_familias_por_apellido,
    listar_inscripciones_de_familia,
)

router = APIRouter(prefix="/familias", tags=["familias"])

# Se recorta antes de medir: " P " tiene un solo caracter y da 422. Un
# caracter de control da 422 en lugar de llegar a Postgres.
TextoApellido = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2),
    AfterValidator(sin_caracteres_de_control),
]


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


@router.get(
    "/{familia_id}/inscripciones",
    response_model=list[InscripcionDeFamilia],
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
        status.HTTP_404_NOT_FOUND: respuesta_de_error(MENSAJE_FAMILIA_INEXISTENTE),
    },
)
def inscripciones_de_familia(
    familia_id: int,
    _: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> list[InscripcionDeFamilia]:
    """Inscripciones de los hijos de la familia en la temporada vigente. Solo
    el Admin: el 403 llega antes de buscar la familia."""
    try:
        filas = listar_inscripciones_de_familia(sesion, familia_id)
    except FamiliaInexistente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_FAMILIA_INEXISTENTE
        ) from None
    return [InscripcionDeFamilia.model_validate(fila) for fila in filas]
