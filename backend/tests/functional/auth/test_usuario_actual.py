"""Tests de contrato de `GET /api/v1/auth/yo` (change auth-ingreso, tarea 2.1).

Un test por Scenario de la spec delta
`openspec/changes/auth-ingreso/specs/auth/spec.md`:
- Requirement «Identificación del usuario actual por token» (los 10 Scenarios).
- Requirement «Cambio obligatorio de contraseña pendiente», solo el Scenario
  «Con el cambio pendiente igual puede saber quién es».

El `detail` y el encabezado de los 401 los fija design.md:
`Sesión inválida o vencida.` con `WWW-Authenticate: Bearer`.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.core.security import hashear
from app.models.usuario import RolUsuario, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_YO = "/api/v1/auth/yo"
CONTRASENA = "Verano2026"
MENSAJE_SESION_INVALIDA = "Sesión inválida o vencida."
CAMPOS_SECRETOS = {"password_hash", "password_hash_anterior", "intentos_fallidos"}
ALFABETO_BASE64URL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


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


def ingresar(cliente: TestClient, username: str = "jperez") -> str:
    """Hace el login real y devuelve el `access_token`."""
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    token = respuesta.json()["access_token"]
    assert isinstance(token, str) and token != ""
    return token


def pedir_yo(cliente: TestClient, token: str) -> Response:
    return cliente.get(URL_YO, headers={"Authorization": f"Bearer {token}"})


def fabricar_token(sub: str, *, clave: str, vence_en: timedelta) -> str:
    ahora = datetime.now(UTC)
    carga: dict[str, Any] = {"sub": sub, "iat": ahora, "exp": ahora + vence_en}
    return jwt.encode(carga, clave, algorithm="HS256")


def afirmar_401_de_sesion(respuesta: Response) -> None:
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_SESION_INVALIDA
    assert respuesta.headers.get("www-authenticate") == "Bearer"


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


# --- Requirement: Identificación del usuario actual por token ----------------


def test_el_token_del_ingreso_identifica_al_usuario(cliente: TestClient, sesion: Session) -> None:
    crear_usuario(sesion, "jperez")
    token = ingresar(cliente, "jperez")

    respuesta = pedir_yo(cliente, token)

    assert respuesta.status_code == 200
    assert respuesta.json()["username"] == "jperez"


def test_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.get(URL_YO)

    afirmar_401_de_sesion(respuesta)


def test_el_token_adulterado_responde_401(cliente: TestClient, sesion: Session) -> None:
    crear_usuario(sesion, "jperez")
    token = ingresar(cliente, "jperez")
    assert pedir_yo(cliente, token).status_code == 200

    cabecera, carga, firma = token.split(".")
    medio = len(firma) // 2
    original = firma[medio]
    reemplazo = "A" if original != "A" else "B"
    assert reemplazo in ALFABETO_BASE64URL
    firma_adulterada = firma[:medio] + reemplazo + firma[medio + 1 :]
    token_adulterado = f"{cabecera}.{carga}.{firma_adulterada}"
    assert token_adulterado != token

    respuesta = pedir_yo(cliente, token_adulterado)

    afirmar_401_de_sesion(respuesta)


def test_el_token_firmado_con_otra_clave_responde_401(cliente: TestClient, sesion: Session) -> None:
    usuario = crear_usuario(sesion, "jperez")
    assert usuario.activo is True and usuario.intentos_fallidos == 0
    clave_del_sistema = obtener_configuracion().secret_key
    otra_clave = clave_del_sistema + "-otra-clave-distinta"
    assert otra_clave != clave_del_sistema

    token = fabricar_token(str(usuario.id), clave=otra_clave, vence_en=timedelta(hours=1))

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_el_token_vencido_hace_un_minuto_responde_401(cliente: TestClient, sesion: Session) -> None:
    usuario = crear_usuario(sesion, "jperez")
    assert usuario.activo is True and usuario.intentos_fallidos == 0
    token = fabricar_token(
        str(usuario.id),
        clave=obtener_configuracion().secret_key,
        vence_en=timedelta(minutes=-1),
    )

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_el_token_con_sub_inexistente_responde_401(cliente: TestClient, sesion: Session) -> None:
    crear_usuario(sesion, "jperez")
    id_maximo = sesion.execute(select(func.max(Usuario.id))).scalar_one()
    id_inexistente = (id_maximo or 0) + 1000
    existe = sesion.execute(select(Usuario.id).where(Usuario.id == id_inexistente)).first()
    assert existe is None

    token = fabricar_token(
        str(id_inexistente),
        clave=obtener_configuracion().secret_key,
        vence_en=timedelta(hours=1),
    )

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_el_token_con_sub_fuera_del_rango_de_los_ids_responde_401(cliente: TestClient) -> None:
    sub_fuera_de_rango = "9223372036854775808"
    assert int(sub_fuera_de_rango) == 2**63  # uno más que el máximo de BIGINT

    token = fabricar_token(
        sub_fuera_de_rango,
        clave=obtener_configuracion().secret_key,
        vence_en=timedelta(hours=1),
    )

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_el_token_vigente_de_un_usuario_desactivado_despues_del_ingreso_responde_401(
    cliente: TestClient, sesion: Session
) -> None:
    usuario = crear_usuario(sesion, "jperez")
    token = ingresar(cliente, "jperez")
    assert pedir_yo(cliente, token).status_code == 200

    usuario.activo = False
    sesion.flush()

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_el_token_vigente_de_un_usuario_bloqueado_despues_del_ingreso_responde_401(
    cliente: TestClient, sesion: Session
) -> None:
    usuario = crear_usuario(sesion, "jperez")
    token = ingresar(cliente, "jperez")
    assert pedir_yo(cliente, token).status_code == 200

    usuario.intentos_fallidos = 5
    sesion.flush()

    respuesta = pedir_yo(cliente, token)

    afirmar_401_de_sesion(respuesta)


def test_los_datos_del_usuario_actual_no_exponen_secretos(
    cliente: TestClient, sesion: Session
) -> None:
    usuario = crear_usuario(sesion, "jperez", rol=RolUsuario.PROFESOR)
    id_esperado = usuario.id
    token = ingresar(cliente, "jperez")

    respuesta = pedir_yo(cliente, token)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == id_esperado
    assert cuerpo["username"] == "jperez"
    assert cuerpo["nombre"] == "Juan"
    assert cuerpo["apellido"] == "Perez"
    assert cuerpo["rol"] == "profesor"
    assert cuerpo["debe_cambiar_password"] is False
    assert claves_en_todos_los_niveles(cuerpo).isdisjoint(CAMPOS_SECRETOS)


# --- Requirement: Cambio obligatorio de contraseña pendiente -----------------


def test_con_el_cambio_pendiente_igual_puede_saber_quien_es(
    cliente: TestClient, sesion: Session
) -> None:
    crear_usuario(sesion, "jperez", debe_cambiar_password=True)
    token = ingresar(cliente, "jperez")

    respuesta = pedir_yo(cliente, token)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["username"] == "jperez"
    assert cuerpo["debe_cambiar_password"] is True
