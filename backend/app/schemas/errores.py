"""Forma de los errores que la API emite con HTTPException."""

from typing import Any

from pydantic import BaseModel


class MensajeError(BaseModel):
    """Un rechazo con `detail` en castellano, que src/lib/api.ts muestra tal
    cual."""

    detail: str


def respuesta_de_error(mensaje: str) -> dict[str, Any]:
    """Entrada de `responses=` para documentar un rechazo con su mensaje
    exacto en el contrato."""
    return {
        "model": MensajeError,
        "description": mensaje,
        "content": {"application/json": {"example": {"detail": mensaje}}},
    }


class ErrorDeCampo(BaseModel):
    """Un error atado a un campo del pedido, de validacion o de una regla del
    negocio (`type` `regla_de_negocio`)."""

    loc: list[str | int]
    msg: str
    type: str


class ErroresDeCampo(BaseModel):
    """El 422: la lista de errores, cada uno con su campo en `loc`."""

    detail: list[ErrorDeCampo]
