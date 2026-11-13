"""Consulta de familias por el apellido de sus alumnos."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, exists, func, literal, select
from sqlalchemy.orm import Session

from app.models.alumno import Alumno
from app.models.familia import Familia, v_familia_etiqueta

# Tope de la busqueda: la pantalla la usa como autocompletado.
MAXIMO_DE_FAMILIAS = 20

# Caracter de escape del LIKE para el texto del usuario.
_ESCAPE = "\\"


def _escapar_like(texto: str) -> str:
    """Escapa los comodines del LIKE (y el propio escape) para que el texto
    del usuario se compare literal."""
    return (
        texto.replace(_ESCAPE, _ESCAPE * 2).replace("%", _ESCAPE + "%").replace("_", _ESCAPE + "_")
    )


def buscar_familias_por_apellido(sesion: Session, texto: str) -> Sequence[Row[Any]]:
    """Familias con al menos un alumno cuyo apellido empieza con `texto`, sin
    distinguir mayusculas, por etiqueta (desempate por id), a lo sumo 20.

    `texto` llega ya recortado y validado por el router. Todo pasa en SQL: el
    orden por etiqueta y el corte en 20 no se pueden hacer bien en Python sin
    traer todas las coincidencias. El EXISTS evita repetir la familia cuando
    coinciden dos hijos. No hay filtro por grupo para el Profesor (design,
    «Endpoints, roles y filtro del Profesor»).
    """
    patron = literal(_escapar_like(texto) + "%")
    coincide = exists().where(
        Alumno.familia_id == Familia.id,
        # lower() de los dos lados y en la base, como el indice
        # ix_alumno_apellido_lower.
        func.lower(Alumno.apellido).like(func.lower(patron), escape=_ESCAPE),
    )
    etiqueta = v_familia_etiqueta.c.etiqueta
    consulta = (
        select(Familia.id, etiqueta.label("etiqueta"), Familia.categoria)
        .join(v_familia_etiqueta, v_familia_etiqueta.c.familia_id == Familia.id)
        .where(coincide)
        .order_by(etiqueta, Familia.id)
        .limit(MAXIMO_DE_FAMILIAS)
    )
    return sesion.execute(consulta).all()
