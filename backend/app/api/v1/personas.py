"""Rutas de personas. Solo traducen el resultado de app/services/personas.py
a HTTP."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AfterValidator
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, MENSAJE_SIN_PERMISO, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.errores import respuesta_de_error
from app.schemas.personas import PersonaEncontrada
from app.services.personas import buscar_persona_por_dni, normalizar_dni

router = APIRouter(prefix="/personas", tags=["personas"])

MENSAJE_SIN_DNI = "No hay ninguna persona con ese DNI."


def _dni_normalizado(texto: str) -> str:
    """Normaliza el DNI pedido; vacio despues de normalizar es un 422."""
    dni = normalizar_dni(texto)
    if not dni:
        # Type `regla_de_negocio`: el manejador del 422 deja el mensaje intacto.
        raise PydanticCustomError("regla_de_negocio", "Ingresá un DNI.")
    return dni


DniPedido = Annotated[str, AfterValidator(_dni_normalizado)]


@router.get(
    "",
    response_model=PersonaEncontrada,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
        status.HTTP_404_NOT_FOUND: respuesta_de_error(MENSAJE_SIN_DNI),
    },
)
def buscar_persona(
    _: Annotated[
        Usuario,
        Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR, RolUsuario.PROFESOR)),
    ],
    sesion: Annotated[Session, Depends(obtener_sesion)],
    dni: Annotated[DniPedido, Query()],
) -> PersonaEncontrada:
    # Coincidencia exacta y solo id, nombre y apellido: no deja recorrer el
    # padron, por eso no hay filtro por grupo para el Profesor.
    fila = buscar_persona_por_dni(sesion, dni)
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MENSAJE_SIN_DNI)
    return PersonaEncontrada.model_validate(fila)
