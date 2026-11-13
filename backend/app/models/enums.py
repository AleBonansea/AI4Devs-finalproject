"""Tipos enumerados que comparten varias tablas.

Cada uno se declara una sola vez como objeto `Enum` de SQLAlchemy y ese
mismo objeto se reutiliza en cada columna. Asi Postgres tiene un solo tipo
`turno`, no uno por tabla, y una migracion lo crea una sola vez.

Los tipos de una sola tabla (`estado_temporada`, `rol_usuario`) siguen junto
a su modelo.
"""

import enum

from sqlalchemy import Enum


class Turno(enum.StrEnum):
    MANANA = "manana"
    TARDE = "tarde"


class Modalidad(enum.StrEnum):
    MES = "mes"
    QUINCENA = "quincena"
    SEMANA = "semana"
    DIA = "dia"


class CategoriaFamilia(enum.StrEnum):
    SOCIO = "socio"
    EMPLEADO = "empleado"
    NO_SOCIO = "no_socio"


class CalculoCargo(enum.StrEnum):
    MONTO_FIJO = "monto_fijo"
    TARIFARIO = "tarifario"


def _tipo(clase: type[enum.StrEnum], nombre: str) -> Enum:
    # values_callable: sin esto SQLAlchemy manda los NOMBRES de los miembros
    # ('MANANA') y no sus valores ('manana'). Ver la nota en temporada.py.
    return Enum(
        clase,
        name=nombre,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


TIPO_TURNO = _tipo(Turno, "turno")
TIPO_MODALIDAD = _tipo(Modalidad, "modalidad")
# Lo usa descuento_* ahora y `familia` despues: esa migracion no lo vuelve a crear.
TIPO_CATEGORIA_FAMILIA = _tipo(CategoriaFamilia, "categoria_familia")
TIPO_CALCULO_CARGO = _tipo(CalculoCargo, "calculo_cargo")
