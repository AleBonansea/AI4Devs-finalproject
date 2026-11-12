"""Rutas de ingreso. Solo traducen el resultado de app/services/auth.py a
HTTP."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.schemas.auth import LoginEntrada, LoginRespuesta, UsuarioActual
from app.services.auth import CredencialesInvalidas, UsuarioBloqueado, ingresar

router = APIRouter(prefix="/auth", tags=["auth"])

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_BLOQUEADO = "Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña."


@router.post("/login", response_model=LoginRespuesta)
def login(
    entrada: LoginEntrada, sesion: Annotated[Session, Depends(obtener_sesion)]
) -> LoginRespuesta:
    # Publico: es la puerta, no lleva token.
    try:
        ingreso = ingresar(sesion, entrada.username, entrada.password)
    except CredencialesInvalidas:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_CREDENCIALES
        ) from None
    except UsuarioBloqueado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_BLOQUEADO
        ) from None
    return LoginRespuesta(
        access_token=ingreso.token,
        usuario=UsuarioActual.model_validate(ingreso.usuario),
    )
