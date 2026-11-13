"""Tabla de traduccion de los 422 de Pydantic (change familias-y-alumnos,
tarea 9.2, hallazgo del pase adversarial).

`openspec/changes/familias-y-alumnos/design.md`, seccion «Traducción de los
422 de Pydantic», parrafo «La tabla se prueba entera»: se llama a la funcion
pura con cada `type` de la tabla, y con uno desconocido, y se compara el
mensaje exacto. Un `type` mal escrito en la tabla cae al generico sin que
ningun Scenario lo note; este test si lo nota.

Es la unica excepcion a «se prueba por la API»: lo pide el design, y la
interfaz publica es `app.core.errores.mensaje_en_castellano(tipo, mensaje,
ctx)`.

Los `mensaje` y `ctx` de entrada imitan los que arma Pydantic, en ingles,
para que un mensaje que pasara sin traducir se note.
"""

from typing import Any

import pytest

from app.core.errores import mensaje_en_castellano

GENERICO = "El valor no es válido."

CASOS: list[tuple[str, str, dict[str, Any] | None, str]] = [
    # missing
    ("missing", "Field required", None, "Este dato es obligatorio."),
    # string_too_long, too_long: el maximo sale de ctx (dos valores, para que
    # no se apruebe con una constante).
    (
        "string_too_long",
        "String should have at most 80 characters",
        {"max_length": 80},
        "Puede tener hasta 80 caracteres.",
    ),
    (
        "string_too_long",
        "String should have at most 60 characters",
        {"max_length": 60},
        "Puede tener hasta 60 caracteres.",
    ),
    (
        "too_long",
        "List should have at most 10 items after validation, not 11",
        {"field_type": "List", "max_length": 10, "actual_length": 11},
        "Puede tener hasta 10 caracteres.",
    ),
    # string_too_short: con min_length 1 dice «vacío»; con mas, el minimo.
    (
        "string_too_short",
        "String should have at least 1 character",
        {"min_length": 1},
        "No puede quedar vacío.",
    ),
    (
        "string_too_short",
        "String should have at least 2 characters",
        {"min_length": 2},
        "Tiene que tener al menos 2 caracteres.",
    ),
    (
        "string_too_short",
        "String should have at least 3 characters",
        {"min_length": 3},
        "Tiene que tener al menos 3 caracteres.",
    ),
    # fechas
    (
        "date_parsing",
        "Input should be a valid date in the format YYYY-MM-DD, invalid character in year",
        {"error": "invalid character in year"},
        "La fecha no es válida.",
    ),
    (
        "date_from_datetime_parsing",
        "Input should be a valid date or datetime, invalid character in year",
        {"error": "invalid character in year"},
        "La fecha no es válida.",
    ),
    ("date_type", "Input should be a valid date", None, "La fecha no es válida."),
    # enteros
    (
        "int_parsing",
        "Input should be a valid integer, unable to parse string as an integer",
        None,
        "Tiene que ser un número entero.",
    ),
    ("int_type", "Input should be a valid integer", None, "Tiene que ser un número entero."),
    # opciones
    (
        "enum",
        "Input should be 'socio', 'empleado' or 'no_socio'",
        {"expected": "'socio', 'empleado' or 'no_socio'"},
        "El valor no es una de las opciones válidas.",
    ),
    (
        "literal_error",
        "Input should be 'manana' or 'tarde'",
        {"expected": "'manana' or 'tarde'"},
        "El valor no es una de las opciones válidas.",
    ),
    # regla_de_negocio: se deja el mensaje recibido (dos, para que no sea una
    # constante).
    (
        "regla_de_negocio",
        "La fecha de nacimiento no puede ser posterior a hoy.",
        None,
        "La fecha de nacimiento no puede ser posterior a hoy.",
    ),
    (
        "regla_de_negocio",
        "No puede tener caracteres de control.",
        None,
        "No puede tener caracteres de control.",
    ),
    # cualquier otro
    ("tipo_que_no_existe", "Something went wrong", None, GENERICO),
]


@pytest.mark.parametrize(
    ("tipo", "mensaje", "ctx", "esperado"),
    CASOS,
    ids=[f"{c[0]}-{i}" for i, c in enumerate(CASOS)],
)
def test_cada_type_de_la_tabla_da_su_mensaje_en_castellano(
    tipo: str, mensaje: str, ctx: dict[str, Any] | None, esperado: str
) -> None:
    assert mensaje_en_castellano(tipo, mensaje, ctx) == esperado
