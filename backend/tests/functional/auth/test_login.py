"""Tests de contrato de `POST /api/v1/auth/login` (change auth-ingreso, tarea 1.1).

Un test por Scenario de la spec delta
`openspec/changes/auth-ingreso/specs/auth/spec.md`, requirements:
- Ingreso con usuario y contraseña
- Pedido de ingreso malformado
- Credenciales rechazadas sin revelar la causa
- Contador de intentos fallidos
- Usuario bloqueado no ingresa
- Cambio obligatorio de contraseña pendiente (solo «Ingresa con el cambio pendiente»)
"""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models.usuario import RolUsuario, Usuario

URL_LOGIN = "/api/v1/auth/login"
CONTRASENA = "Verano2026"
CONTRASENA_INCORRECTA = "Otra1234"
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_BLOQUEADO = "Usuario bloqueado. Pedile a un Admin que blanquee tu contraseña."
CAMPOS_SECRETOS = {"password_hash", "password_hash_anterior", "intentos_fallidos"}


def crear_usuario(
    sesion: Session,
    username: str = "jperez",
    *,
    contrasena: str = CONTRASENA,
    rol: RolUsuario = RolUsuario.COORDINADOR,
    activo: bool = True,
    intentos_fallidos: int = 0,
    debe_cambiar_password: bool = False,
) -> Usuario:
    usuario = Usuario(
        username=username,
        password_hash=hashear(contrasena),
        debe_cambiar_password=debe_cambiar_password,
        intentos_fallidos=intentos_fallidos,
        nombre="Juan",
        apellido="Perez",
        rol=rol,
        activo=activo,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario


def intentos_en_base(sesion: Session, username: str) -> int:
    sesion.expire_all()
    return sesion.execute(
        select(Usuario.intentos_fallidos).where(Usuario.username == username)
    ).scalar_one()


def claves_en_todos_los_niveles(valor: Any) -> set[str]:
    claves: set[str] = set()
    if isinstance(valor, dict):
        for clave, sub in valor.items():
            claves.add(clave)
            claves |= claves_en_todos_los_niveles(sub)
    elif isinstance(valor, list):
        for sub in valor:
            claves |= claves_en_todos_los_niveles(sub)
    return claves


# --- Requirement: Ingreso con usuario y contraseña ---------------------------


def test_el_ingreso_correcto_devuelve_token_y_usuario_sin_secretos(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", rol=RolUsuario.COORDINADOR)

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": CONTRASENA})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert isinstance(cuerpo["access_token"], str) and cuerpo["access_token"] != ""
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["rol"] == "coordinador"
    assert cuerpo["usuario"]["debe_cambiar_password"] is False
    assert set(cuerpo.keys()) == {"access_token", "token_type", "usuario"}
    assert claves_en_todos_los_niveles(cuerpo).isdisjoint(CAMPOS_SECRETOS)


def test_el_usuario_con_mayusculas_o_espacios_ingresa_normalizado(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez")

    respuesta = cliente.post(URL_LOGIN, json={"username": " JPerez ", "password": CONTRASENA})

    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["username"] == "jperez"


def test_la_contrasena_con_otra_capitalizacion_es_rechazada(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez")

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": "verano2026"})

    assert respuesta.status_code == 401


def test_la_contrasena_vacia_responde_422_sin_token(cliente: TestClient) -> None:
    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": ""})

    assert respuesta.status_code == 422
    assert "access_token" not in claves_en_todos_los_niveles(respuesta.json())


def test_el_usuario_con_un_caracter_de_control_responde_422_sin_token(
    cliente: TestClient, sesion: Session
) -> None:
    # Existe `jperez` con esa contraseña: si el NUL se descartara en silencio,
    # el pedido entraría con 200. El 422 tiene que venir del carácter de control.
    crear_usuario(sesion, "jperez")
    username = "jp\u0000erez"
    assert "\x00" in username

    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})

    assert respuesta.status_code == 422, respuesta.text
    assert "access_token" not in claves_en_todos_los_niveles(respuesta.json())


def test_el_usuario_de_solo_espacios_responde_422_sin_token(cliente: TestClient) -> None:
    respuesta = cliente.post(URL_LOGIN, json={"username": "   ", "password": CONTRASENA})

    # El 422 exacto: un 401 de credenciales no cumple el Scenario.
    assert respuesta.status_code == 422, respuesta.text
    assert "access_token" not in claves_en_todos_los_niveles(respuesta.json())


# --- Requirement: Credenciales rechazadas sin revelar la causa ---------------


def test_la_contrasena_incorrecta_responde_401_con_mensaje_generico_sin_token(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez")

    respuesta = cliente.post(
        URL_LOGIN, json={"username": "jperez", "password": CONTRASENA_INCORRECTA}
    )

    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == MENSAJE_CREDENCIALES
    assert "access_token" not in cuerpo


def test_el_usuario_inexistente_responde_401_con_mensaje_generico(
    cliente: TestClient, sesion: Session
) -> None:
    existe = sesion.execute(select(Usuario.id).where(Usuario.username == "nadie")).first()
    assert existe is None

    respuesta = cliente.post(URL_LOGIN, json={"username": "nadie", "password": CONTRASENA})

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_CREDENCIALES


def test_el_usuario_desactivado_con_contrasena_correcta_responde_401_generico_sin_token(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "mgomez", activo=False)

    respuesta = cliente.post(URL_LOGIN, json={"username": "mgomez", "password": CONTRASENA})

    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == MENSAJE_CREDENCIALES
    assert "access_token" not in cuerpo


# --- Requirement: Contador de intentos fallidos ------------------------------


def test_un_ingreso_incorrecto_incrementa_el_contador_en_uno(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=2)

    respuesta = cliente.post(
        URL_LOGIN, json={"username": "jperez", "password": CONTRASENA_INCORRECTA}
    )

    assert respuesta.status_code == 401
    assert intentos_en_base(sesion, "jperez") == 3


def test_un_ingreso_correcto_pone_el_contador_en_cero(cliente: TestClient, sesion: Session) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=4)

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": CONTRASENA})

    assert respuesta.status_code == 200
    assert intentos_en_base(sesion, "jperez") == 0


def test_el_quinto_ingreso_incorrecto_responde_401_y_deja_el_contador_en_cinco(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=4)

    respuesta = cliente.post(
        URL_LOGIN, json={"username": "jperez", "password": CONTRASENA_INCORRECTA}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_CREDENCIALES
    assert intentos_en_base(sesion, "jperez") == 5


def test_el_ingreso_de_un_usuario_desactivado_no_toca_el_contador(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "mgomez", activo=False, intentos_fallidos=1)

    respuesta = cliente.post(
        URL_LOGIN, json={"username": "mgomez", "password": CONTRASENA_INCORRECTA}
    )

    assert respuesta.status_code == 401
    assert intentos_en_base(sesion, "mgomez") == 1


# --- Requirement: Usuario bloqueado no ingresa -------------------------------


def test_el_bloqueado_con_contrasena_correcta_recibe_403_sin_token_y_el_contador_sigue(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=5)

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": CONTRASENA})

    assert respuesta.status_code == 403
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == MENSAJE_BLOQUEADO
    assert "access_token" not in cuerpo
    assert intentos_en_base(sesion, "jperez") == 5


def test_el_bloqueado_con_contrasena_incorrecta_recibe_403_y_el_contador_sigue(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=7)

    respuesta = cliente.post(
        URL_LOGIN, json={"username": "jperez", "password": CONTRASENA_INCORRECTA}
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_BLOQUEADO
    assert intentos_en_base(sesion, "jperez") == 7


def test_con_cuatro_intentos_todavia_ingresa_con_token(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", intentos_fallidos=4)

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": CONTRASENA})

    assert respuesta.status_code == 200
    token = respuesta.json()["access_token"]
    assert isinstance(token, str) and token != ""


# --- Requirement: Cambio obligatorio de contraseña pendiente -----------------


def test_con_el_cambio_pendiente_ingresa_y_la_respuesta_lo_indica(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", debe_cambiar_password=True, intentos_fallidos=2)
    assert intentos_en_base(sesion, "jperez") == 2

    respuesta = cliente.post(URL_LOGIN, json={"username": "jperez", "password": CONTRASENA})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert isinstance(cuerpo["access_token"], str) and cuerpo["access_token"] != ""
    assert cuerpo["usuario"]["debe_cambiar_password"] is True
    assert intentos_en_base(sesion, "jperez") == 0
