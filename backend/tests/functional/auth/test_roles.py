"""Tests de contrato de `usuario_habilitado` y `exigir_rol` (change auth-ingreso, tarea 3.1).

Un test por Scenario de la spec delta
`openspec/changes/auth-ingreso/specs/auth/spec.md`:
- Requirement «Declaración de roles por endpoint» (los 4 Scenarios).
- Requirement «Cambio obligatorio de contraseña pendiente», los Scenarios
  «Con el cambio pendiente no puede hacer nada más», «Con el cambio
  pendiente tampoco pasa un endpoint de su rol» y «Con el cambio pendiente,
  el 403 de cambio gana al de rol».

Todavía no hay endpoints de negocio. Como fija design.md («Cómo se prueba
`exigir_rol` sin endpoints de negocio»), el test monta un `APIRouter` de
sonda sobre una instancia de FastAPI propia, con el mismo override de
`obtener_sesion` que el `cliente` de conftest, y lo llama por HTTP. No se
agrega ninguna ruta a la aplicación real.

Los tokens salen del login real `POST /api/v1/auth/login` de la app real.

Mensajes fijados por la spec y design.md:
- 401: `Sesión inválida o vencida.` con `WWW-Authenticate: Bearer`.
- 403 de cambio pendiente: `Tenés que cambiar tu contraseña antes de continuar.`
- 403 de rol: `No tenés permiso para esta operación.`
"""

from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import exigir_rol
from app.core.security import hashear
from app.main import app
from app.models.usuario import RolUsuario, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_YO = "/api/v1/auth/yo"
CONTRASENA = "Verano2026"

MENSAJE_SESION_INVALIDA = "Sesión inválida o vencida."
MENSAJE_CAMBIO_PENDIENTE = "Tenés que cambiar tu contraseña antes de continuar."
MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."

# Rutas de la sonda.
URL_ADMIN_O_COORDINADOR = "/sonda/admin-o-coordinador"
URL_SOLO_ADMIN = "/sonda/solo-admin"
URL_TODOS_LOS_ROLES = "/sonda/todos-los-roles"


# --- Sonda ---------------------------------------------------------------------


def _router_de_sonda() -> APIRouter:
    router = APIRouter(prefix="/sonda")

    # Forma `usuario: Usuario = Depends(exigir_rol(...))`, escrita con
    # Annotated. Devuelve el username que recibió de la dependencia, para
    # que un 200 pruebe que pasó el usuario del token y no una respuesta fija.
    @router.get("/admin-o-coordinador")
    def admin_o_coordinador(
        usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR))],
    ) -> dict[str, str]:
        return {"username": usuario.username}

    @router.get("/solo-admin")
    def solo_admin(
        usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    ) -> dict[str, str]:
        return {"username": usuario.username}

    # Forma `dependencies=[...]` del decorador.
    @router.get(
        "/todos-los-roles",
        dependencies=[
            Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR, RolUsuario.PROFESOR))
        ],
    )
    def todos_los_roles() -> dict[str, bool]:
        return {"ok": True}

    return router


@pytest.fixture
def sonda(cliente: TestClient) -> Iterator[TestClient]:
    """Cliente de una app FastAPI propia del test, con solo las rutas de sonda.

    Reutiliza el override de `obtener_sesion` que el fixture `cliente` acaba de
    instalar en la app real, así la sonda ve los usuarios que el test preparó
    con `sesion`, con la misma sesión por petición que usa la API real.
    """
    app_sonda = FastAPI()
    app_sonda.include_router(_router_de_sonda())
    app_sonda.dependency_overrides[obtener_sesion] = app.dependency_overrides[obtener_sesion]
    try:
        with TestClient(app_sonda) as c:
            yield c
    finally:
        app_sonda.dependency_overrides.clear()


# --- Ayudas --------------------------------------------------------------------


def crear_usuario(
    sesion: Session,
    username: str,
    *,
    rol: RolUsuario,
    debe_cambiar_password: bool = False,
) -> Usuario:
    usuario = Usuario(
        username=username,
        password_hash=hashear(CONTRASENA),
        debe_cambiar_password=debe_cambiar_password,
        intentos_fallidos=0,
        nombre="Juan",
        apellido="Perez",
        rol=rol,
        activo=True,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario


def ingresar(cliente: TestClient, username: str) -> str:
    """Hace el login real y devuelve el `access_token`."""
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    token = respuesta.json()["access_token"]
    assert isinstance(token, str) and token != ""
    return token


def con_token(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def afirmar_403(respuesta: Response, detail: str) -> None:
    assert respuesta.status_code == 403, respuesta.text
    assert respuesta.json()["detail"] == detail


# --- Requirement: Declaración de roles por endpoint ---------------------------


def test_el_rol_declarado_pasa(cliente: TestClient, sonda: TestClient, sesion: Session) -> None:
    crear_usuario(sesion, "coordi", rol=RolUsuario.COORDINADOR)
    token = ingresar(cliente, "coordi")

    respuesta = sonda.get(URL_ADMIN_O_COORDINADOR, headers=con_token(token))

    assert respuesta.status_code == 200, respuesta.text
    # La dependencia entregó al endpoint el usuario del token.
    assert respuesta.json() == {"username": "coordi"}


def test_el_rol_no_declarado_recibe_403_sin_permiso(
    cliente: TestClient, sonda: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "profe", rol=RolUsuario.PROFESOR)
    token = ingresar(cliente, "profe")
    # El token es válido: el rechazo que sigue es por rol, no por sesión.
    assert cliente.get(URL_YO, headers=con_token(token)).status_code == 200

    respuesta = sonda.get(URL_ADMIN_O_COORDINADOR, headers=con_token(token))

    afirmar_403(respuesta, MENSAJE_SIN_PERMISO)


def test_el_coordinador_recibe_403_sin_permiso_en_un_endpoint_solo_para_admin(
    cliente: TestClient, sonda: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "coordi", rol=RolUsuario.COORDINADOR)
    crear_usuario(sesion, "admin1", rol=RolUsuario.ADMIN)
    token_coordinador = ingresar(cliente, "coordi")
    token_admin = ingresar(cliente, "admin1")

    respuesta = sonda.get(URL_SOLO_ADMIN, headers=con_token(token_coordinador))

    afirmar_403(respuesta, MENSAJE_SIN_PERMISO)
    # Contraste del lado de adentro: la misma ruta deja pasar al rol declarado,
    # así que el 403 no es una respuesta fija de la ruta.
    respuesta_admin = sonda.get(URL_SOLO_ADMIN, headers=con_token(token_admin))
    assert respuesta_admin.status_code == 200, respuesta_admin.text
    assert respuesta_admin.json() == {"username": "admin1"}


def test_sin_token_un_endpoint_con_roles_responde_401(sonda: TestClient) -> None:
    respuesta = sonda.get(URL_SOLO_ADMIN)

    assert respuesta.status_code == 401, respuesta.text
    assert respuesta.json()["detail"] == MENSAJE_SESION_INVALIDA
    assert respuesta.headers.get("www-authenticate") == "Bearer"


# --- Requirement: Cambio obligatorio de contraseña pendiente -----------------


def test_con_el_cambio_pendiente_un_endpoint_protegido_responde_403_de_cambio_pendiente(
    cliente: TestClient, sonda: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", rol=RolUsuario.PROFESOR, debe_cambiar_password=True)
    token = ingresar(cliente, "jperez")
    # El token es válido (el exento /yo lo acepta): el rechazo no es de sesión.
    assert cliente.get(URL_YO, headers=con_token(token)).status_code == 200

    respuesta = sonda.get(URL_TODOS_LOS_ROLES, headers=con_token(token))

    # El rol profesor está declarado, así que el único 403 posible es el del
    # cambio pendiente; el `detail` lo distingue del de rol.
    afirmar_403(respuesta, MENSAJE_CAMBIO_PENDIENTE)


def test_con_el_cambio_pendiente_el_admin_tampoco_pasa_un_endpoint_de_su_rol(
    cliente: TestClient, sonda: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "admin1", rol=RolUsuario.ADMIN, debe_cambiar_password=True)
    token = ingresar(cliente, "admin1")
    assert cliente.get(URL_YO, headers=con_token(token)).status_code == 200

    respuesta = sonda.get(URL_SOLO_ADMIN, headers=con_token(token))

    afirmar_403(respuesta, MENSAJE_CAMBIO_PENDIENTE)


def test_con_el_cambio_pendiente_el_403_de_cambio_gana_al_de_rol(
    cliente: TestClient, sonda: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "profe", rol=RolUsuario.PROFESOR, debe_cambiar_password=True)
    token = ingresar(cliente, "profe")
    # El token es válido (el exento /yo lo acepta): el rechazo no es de sesión.
    assert cliente.get(URL_YO, headers=con_token(token)).status_code == 200

    respuesta = sonda.get(URL_SOLO_ADMIN, headers=con_token(token))

    # El profesor no está declarado en la ruta y además tiene el cambio
    # pendiente: tiene que ganar el `detail` de cambio pendiente, no el de rol.
    afirmar_403(respuesta, MENSAJE_CAMBIO_PENDIENTE)
