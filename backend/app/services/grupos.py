"""Consulta de los grupos donde se puede inscribir a un alumno."""

from collections.abc import Sequence
from datetime import date
from typing import Any

from sqlalchemy import Row, and_, false, literal, select
from sqlalchemy.orm import Session

from app.models.grupo import Grupo, GrupoProfesor
from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import RolUsuario, Usuario


def listar_grupos_para_inscribir(
    sesion: Session, usuario: Usuario, fecha_nacimiento: date | None
) -> Sequence[Row[Any]]:
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
    return sesion.execute(consulta).all()
