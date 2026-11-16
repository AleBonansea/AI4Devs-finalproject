"""Consulta de los grupos donde se puede inscribir a un alumno."""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from sqlalchemy import and_, false, literal, select
from sqlalchemy.orm import Session

from app.models.grupo import Grupo, GrupoProfesor
from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import RolUsuario, Usuario


def edad_del_grupo(
    anio_referencia: int, nacimiento_desde: date, nacimiento_hasta: date
) -> tuple[int, int]:
    """Rango de edades `(desde, hasta)` que cubre el rango de nacimiento.

    En años enteros: el año de referencia menos el año de nacimiento, sin
    mirar mes ni dia. Es a proposito y no una aproximacion: una edad cumplida
    a una fecha exacta daria tres edades para un rango de dos años completos
    (ver el design del change menu-lateral-y-edad-de-grupos). El nacimiento
    mas tardio da la edad menor.
    """
    return anio_referencia - nacimiento_hasta.year, anio_referencia - nacimiento_desde.year


def listar_grupos_para_inscribir(
    sesion: Session, usuario: Usuario, fecha_nacimiento: date | None
) -> Sequence[Mapping[str, Any]]:
    """Grupos activos de la temporada vigente, por turno y nombre.

    `sugerido` se calcula en la misma consulta: la fecha dentro del rango,
    con los dos extremos incluidos (BETWEEN). Sin fecha, false para todos.
    La sugerencia no filtra: vienen los mismos grupos con o sin fecha.
    """
    sugerido = (
        literal(fecha_nacimiento).between(Grupo.nacimiento_desde, Grupo.nacimiento_hasta)
        if fecha_nacimiento is not None
        else false()
    )

    consulta = (
        select(
            Grupo.id,
            Grupo.nombre,
            Grupo.turno,
            Grupo.nacimiento_desde,
            Grupo.nacimiento_hasta,
            Temporada.nombre.label("temporada_nombre"),
            sugerido.label("sugerido"),
        )
        .join(Temporada, Temporada.id == Grupo.temporada_id)
        .where(Temporada.estado == EstadoTemporada.VIGENTE, Grupo.activo.is_(True))
        # El orden del tipo enumerado de Postgres: `manana` antes que `tarde`.
        .order_by(Grupo.turno, Grupo.nombre)
    )
    if usuario.rol == RolUsuario.PROFESOR:
        # El filtro del Profesor va en la consulta: nunca recibe filas de
        # grupos ajenos, ni siquiera para descartarlas.
        consulta = consulta.join(
            GrupoProfesor,
            and_(GrupoProfesor.grupo_id == Grupo.id, GrupoProfesor.usuario_id == usuario.id),
        )
    filas = sesion.execute(consulta).all()
    # El año de referencia es el primer año del nombre de la temporada (2026
    # para «2026-27»), no el de su fecha de inicio: los 4 primeros caracteres,
    # que el CHECK de la base garantiza numericos.
    resultado: list[dict[str, Any]] = []
    for fila in filas:
        edad_desde, edad_hasta = edad_del_grupo(
            int(fila.temporada_nombre[:4]), fila.nacimiento_desde, fila.nacimiento_hasta
        )
        resultado.append({**fila._mapping, "edad_desde": edad_desde, "edad_hasta": edad_hasta})
    return resultado
