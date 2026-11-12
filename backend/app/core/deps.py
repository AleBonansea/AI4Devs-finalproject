"""Dependencias de FastAPI para identificar al usuario de cada peticion.

El token lleva solo el id (ver design de auth-ingreso): el usuario se relee
de la base en cada peticion, para que desactivarlo o bloquearlo corte su
sesion en el acto y no recien cuando el token venza.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.security import leer_token
from app.models.usuario import Usuario

MENSAJE_SESION_INVALIDA = "Sesión inválida o vencida."

# auto_error=False: sin token, HTTPBearer devolveria su propio error con otro
# mensaje. Asi el 401 es uno solo y lo arma esta dependencia.
_bearer = HTTPBearer(auto_error=False)


def _sesion_invalida() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=MENSAJE_SESION_INVALIDA,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obtener_usuario_actual(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> Usuario:
    """El usuario dueño del token. No rechaza el cambio de contraseña
    pendiente: la usan solo los endpoints exentos de esa exigencia.

    Todos los rechazos son el mismo 401, para no revelar si el token era
    invalido, de un usuario inexistente o de uno desactivado.
    """
    if credenciales is None:
        raise _sesion_invalida()

    try:
        carga = leer_token(credenciales.credentials)
    except jwt.PyJWTError:
        raise _sesion_invalida() from None

    try:
        id_usuario = int(carga["sub"])
    except (KeyError, TypeError, ValueError):
        raise _sesion_invalida() from None

    usuario = sesion.get(Usuario, id_usuario)
    if usuario is None or not usuario.activo or usuario.bloqueado:
        raise _sesion_invalida()
    return usuario
