"""Rechazos de reglas del negocio atribuibles a un campo del pedido.

Se responden con la misma forma que el 422 de validacion (ver el manejador
en app/main.py), asi src/lib/api.ts los reparte por campo sin distinguirlos.
Las reglas sin campo (el permiso del Profesor) siguen siendo HTTPException.

Tambien vive aca la traduccion del `msg` de los 422 de Pydantic a castellano.
"""

from typing import Any

# Ruta del campo dentro del cuerpo, sin el "body" inicial: ("personas", 0, "dni").
Ubicacion = tuple[str | int, ...]


class ReglaIncumplida(Exception):
    """Una o mas reglas incumplidas, cada una con su campo y su mensaje."""

    def __init__(self, errores: list[tuple[Ubicacion, str]]) -> None:
        super().__init__(errores)
        self.errores = errores


# Mensaje fijo por `type` de error de Pydantic. Los de largo maximo se arman
# aparte porque llevan el tope de `ctx`.
_MENSAJES_POR_TIPO: dict[str, str] = {
    "missing": "Este dato es obligatorio.",
    "string_too_short": "No puede quedar vacío.",
    "date_parsing": "La fecha no es válida.",
    "date_from_datetime_parsing": "La fecha no es válida.",
    "date_type": "La fecha no es válida.",
    "int_parsing": "Tiene que ser un número entero.",
    "int_type": "Tiene que ser un número entero.",
    "enum": "El valor no es una de las opciones válidas.",
    "literal_error": "El valor no es una de las opciones válidas.",
}

# `too_long` aparece en lugar de `string_too_long` cuando el tope de un
# `Field` se aplica despues de un `BeforeValidator` (el username del login).
_TIPOS_DE_LARGO_MAXIMO = frozenset({"string_too_long", "too_long"})

# Type propio de los validadores y de ReglaIncumplida: su mensaje ya esta en
# castellano y pasa intacto.
TIPO_REGLA_DE_NEGOCIO = "regla_de_negocio"

MENSAJE_GENERICO = "El valor no es válido."


def mensaje_en_castellano(tipo: str, mensaje: str, ctx: dict[str, Any] | None) -> str:
    """El `msg` en castellano de un error de validacion, segun su `type`."""
    if tipo == TIPO_REGLA_DE_NEGOCIO:
        return mensaje
    if tipo in _TIPOS_DE_LARGO_MAXIMO and ctx and "max_length" in ctx:
        return f"Puede tener hasta {ctx['max_length']} caracteres."
    # Con un minimo mayor que uno, "vacio" confundiria: un apellido de una
    # letra en la busqueda no esta vacio. Con minimo 1 o sin ctx, sigue la tabla.
    if tipo == "string_too_short" and ctx and ctx.get("min_length", 1) > 1:
        return f"Tiene que tener al menos {ctx['min_length']} caracteres."
    return _MENSAJES_POR_TIPO.get(tipo, MENSAJE_GENERICO)
