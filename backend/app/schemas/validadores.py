"""Validadores de texto reutilizables por los esquemas y los parametros de
las rutas."""

import unicodedata

from pydantic_core import PydanticCustomError


def tiene_caracteres_de_control(valor: str) -> bool:
    """Si el texto tiene algun caracter de control (categoria Unicode Cc)."""
    return any(unicodedata.category(c) == "Cc" for c in valor)


def sin_caracteres_de_control(valor: str) -> str:
    """Rechaza un texto con caracteres de control.

    Un NUL llega a Postgres, que lo rechaza, y la API respondia 500. Type
    `regla_de_negocio`: el manejador del 422 deja el mensaje intacto.
    """
    if tiene_caracteres_de_control(valor):
        raise PydanticCustomError("regla_de_negocio", "No puede tener caracteres de control.")
    return valor
