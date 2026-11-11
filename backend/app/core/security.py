from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import obtener_configuracion

ALGORITMO = "HS256"

# argon2, no bcrypt: el sistema guarda datos de menores y la contrasena es
# la unica puerta. bcrypt tiene limite de 72 bytes y es mas barato de
# atacar con hardware dedicado.
_hasher = PasswordHash.recommended()


def hashear(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar(contrasena: str, hash_guardado: str) -> bool:
    return _hasher.verify(contrasena, hash_guardado)


def crear_token(asunto: str, extra: dict[str, Any] | None = None) -> str:
    cfg = obtener_configuracion()
    ahora = datetime.now(UTC)
    carga: dict[str, Any] = {
        "sub": asunto,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=cfg.access_token_expire_minutes),
    }
    if extra:
        carga.update(extra)
    return jwt.encode(carga, cfg.secret_key, algorithm=ALGORITMO)


def leer_token(token: str) -> dict[str, Any]:
    """Devuelve la carga del token. Lanza jwt.PyJWTError si no es valido o
    si vencio; quien llama traduce eso a un 401."""
    cfg = obtener_configuracion()
    resultado: dict[str, Any] = jwt.decode(token, cfg.secret_key, algorithms=[ALGORITMO])
    return resultado
