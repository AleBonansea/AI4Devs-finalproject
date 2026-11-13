"""Esquemas de entrada y salida del ingreso."""

import unicodedata
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field
from pydantic_core import PydanticCustomError

from app.models.usuario import RolUsuario
from app.schemas.validadores import tiene_caracteres_de_control


def _normalizar_username(valor: object) -> object:
    # Corre antes de la validacion de tipo y largo, asi un username de solo
    # espacios queda vacio y da 422. Lo que no es texto pasa sin tocar y lo
    # rechaza la validacion de tipo.
    if isinstance(valor, str):
        return valor.strip().lower()
    return valor


def _sin_caracteres_de_control(valor: str) -> str:
    # Un NUL llegaba a Postgres, que lo rechaza, y el login respondia 500.
    # El mensaje propio del login esta fijado en la spec de auth.
    if tiene_caracteres_de_control(valor):
        # Type `regla_de_negocio`: el manejador del 422 deja el mensaje intacto.
        raise PydanticCustomError(
            "regla_de_negocio", "El usuario no puede tener caracteres de control."
        )
    return valor


def _sin_surrogates(valor: str) -> str:
    # FastAPI decodifica el cuerpo con json.loads, que acepta un surrogate
    # suelto escrito como escape, y Pydantic valida el str ya decodificado
    # sin rechazarlo. Llegaba a Postgres y el login respondia 500.
    if any(unicodedata.category(c) == "Cs" for c in valor):
        raise PydanticCustomError("regla_de_negocio", "El texto tiene un carácter inválido.")
    return valor


# Orden: BeforeValidator (normaliza) -> largo de Field -> AfterValidator.
# El largo se mide sobre el valor ya normalizado. 60 es el ancho de la
# columna usuario.username.
Username = Annotated[
    str,
    BeforeValidator(_normalizar_username),
    Field(min_length=1, max_length=60),
    AfterValidator(_sin_caracteres_de_control),
    AfterValidator(_sin_surrogates),
]


class LoginEntrada(BaseModel):
    # JSON y no formulario OAuth2: src/lib/api.ts habla JSON en todo lo demas.
    username: Username
    # Sin normalizar. El tope acota el costo de argon2 en un endpoint publico.
    password: Annotated[str, Field(min_length=1, max_length=128), AfterValidator(_sin_surrogates)]


class UsuarioActual(BaseModel):
    """El usuario que acaba de ingresar, tal como lo ve el mismo. Sin hash
    ni contador de intentos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nombre: str
    apellido: str
    rol: RolUsuario
    debe_cambiar_password: bool


class LoginRespuesta(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    usuario: UsuarioActual
