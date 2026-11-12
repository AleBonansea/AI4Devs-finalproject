"""Dependencias de FastAPI para identificar al usuario de cada peticion.

El token lleva solo el id (ver design de auth-ingreso): el usuario se relee
de la base en cada peticion, para que desactivarlo o bloquearlo corte su
sesion en el acto y no recien cuando el token venza.
"""

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.security import leer_token
from app.models.usuario import RolUsuario, Usuario

MENSAJE_SESION_INVALIDA = "Sesión inválida o vencida."
MENSAJE_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar."
MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."

# Tope de la columna BIGINT de usuario.id. Un sub mas grande hacia fallar a
# Postgres y respondia 500; los ids son positivos.
_ID_MAXIMO = 2**63 - 1

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
    if not 1 <= id_usuario <= _ID_MAXIMO:
        raise _sesion_invalida()

    usuario = sesion.get(Usuario, id_usuario)
    if usuario is None or not usuario.activo or usuario.bloqueado:
        raise _sesion_invalida()
    return usuario


def usuario_habilitado(
    usuario: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> Usuario:
    """El usuario del token, siempre que no tenga el cambio de contraseña
    pendiente. Va encadenada despues de `obtener_usuario_actual`, asi el 401
    gana a este 403.
    """
    if usuario.debe_cambiar_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MENSAJE_CAMBIO_PENDIENTE,
        )
    return usuario


def exigir_rol(*roles: RolUsuario) -> Callable[[Usuario], Usuario]:
    """Fabrica de la dependencia que deja pasar solo a los roles declarados.

    Va sobre `usuario_habilitado`: un usuario con el cambio pendiente recibe
    ese 403 antes que el de rol, y no se entera de que roles usa el endpoint.
    Sirve como parametro (`Annotated[Usuario, Depends(exigir_rol(...))]`) o
    en `dependencies=[Depends(exigir_rol(...))]` del decorador.
    """
    permitidos = frozenset(roles)

    def _verificar_rol(
        usuario: Annotated[Usuario, Depends(usuario_habilitado)],
    ) -> Usuario:
        if usuario.rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MENSAJE_SIN_PERMISO,
            )
        return usuario

    return _verificar_rol
