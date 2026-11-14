"""La asistencia de un grupo en una fecha.

Las reglas van en un orden fijo (design, «El servicio: reglas en un orden
fijo»): permiso del Profesor (dependencia), grupo, fecha dentro de la
temporada y recien entonces se lee.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alumno import Alumno, Inscripcion
from app.models.asistencia import Asistencia
from app.models.grupo import Grupo
from app.models.temporada import Temporada
from app.schemas.asistencias import AlumnoEnAsistencia, AsistenciaDelGrupo
from app.services.comunes import id_posible

MENSAJE_GRUPO_INEXISTENTE = "El grupo no existe."


class GrupoInexistente(Exception):
    """El grupo del path no existe."""


class FechaFueraDeTemporada(Exception):
    """La fecha no esta entre el inicio y el cierre de la temporada del grupo."""

    def __init__(self, inicio: date, cierre: date) -> None:
        super().__init__(inicio, cierre)
        self.mensaje = (
            "La fecha está fuera de la temporada del grupo, "
            f"del {inicio:%d/%m/%Y} al {cierre:%d/%m/%Y}."
        )


def _leer_alumnos(sesion: Session, grupo_id: int, fecha: date) -> list[AlumnoEnAsistencia]:
    """Los inscriptos del grupo con su marca de esa fecha (None si no se tomo).

    El LEFT JOIN da el None; el id final desempata homonimos para que el
    orden sea estable.
    """
    filas = sesion.execute(
        select(Inscripcion.id, Alumno.nombre, Alumno.apellido, Asistencia.presente)
        .join(Alumno, Alumno.id == Inscripcion.alumno_id)
        .outerjoin(
            Asistencia,
            (Asistencia.inscripcion_id == Inscripcion.id) & (Asistencia.fecha == fecha),
        )
        .where(Inscripcion.grupo_id == grupo_id)
        .order_by(Alumno.apellido, Alumno.nombre, Inscripcion.id)
    ).all()
    return [
        AlumnoEnAsistencia(inscripcion_id=i, nombre=n, apellido=a, presente=p)
        for i, n, a, p in filas
    ]


def abrir_asistencia(sesion: Session, grupo_id: int, fecha: date) -> AsistenciaDelGrupo:
    """La lista del grupo para la fecha. Levanta GrupoInexistente (404) o
    FechaFueraDeTemporada (422). Un grupo cerrado o inactivo se puede abrir."""
    fila = (
        sesion.execute(
            select(Grupo.nombre, Grupo.turno, Temporada.fecha_inicio, Temporada.fecha_cierre)
            .join(Temporada, Temporada.id == Grupo.temporada_id)
            .where(Grupo.id == grupo_id)
        ).one_or_none()
        if id_posible(grupo_id)
        else None
    )
    if fila is None:
        raise GrupoInexistente
    nombre, turno, inicio, cierre = fila
    if not inicio <= fecha <= cierre:
        raise FechaFueraDeTemporada(inicio, cierre)
    return AsistenciaDelGrupo(
        grupo_id=grupo_id,
        grupo=nombre,
        turno=turno,
        fecha=fecha,
        alumnos=_leer_alumnos(sesion, grupo_id, fecha),
    )
