"""Esquemas de entrada y salida del ingreso."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.usuario import RolUsuario


class LoginEntrada(BaseModel):
    # JSON y no formulario OAuth2: src/lib/api.ts habla JSON en todo lo demas.
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


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
