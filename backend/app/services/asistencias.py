"""La asistencia de un grupo en una fecha.

Las reglas van en un orden fijo (design, «El servicio: reglas en un orden
fijo»): permiso del Profesor (dependencia), grupo, fecha dentro de la
temporada y recien entonces se lee.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errores import ReglaIncumplida, Ubicacion
from app.models.alumno import Alumno, Inscripcion
from app.models.asistencia import Asistencia
from app.models.enums import Turno
from app.models.grupo import Grupo
from app.models.temporada import EstadoTemporada, Temporada
from app.models.usuario import Usuario
from app.schemas.asistencias import AlumnoEnAsistencia, AsistenciaDelGrupo, AsistenciaEntrada
from app.services.comunes import id_posible

MENSAJE_GRUPO_INEXISTENTE = "El grupo no existe."


class GrupoInexistente(Exception):
    """El grupo del path no existe."""


class TemporadaCerrada(Exception):
    """El grupo es de una temporada cerrada: solo consulta."""

    mensaje = "El grupo es de una temporada cerrada, que queda solo para consulta."


class GrupoInactivo(Exception):
    """El grupo esta desactivado."""

    mensaje = "El grupo no está activo."


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


def _armar(
    sesion: Session, grupo_id: int, nombre: str, turno: Turno, fecha: date
) -> AsistenciaDelGrupo:
    return AsistenciaDelGrupo(
        grupo_id=grupo_id,
        grupo=nombre,
        turno=turno,
        fecha=fecha,
        alumnos=_leer_alumnos(sesion, grupo_id, fecha),
    )


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
    return _armar(sesion, grupo_id, nombre, turno, fecha)


def _errores_del_cuerpo(
    sesion: Session, grupo_id: int, entrada: AsistenciaEntrada
) -> list[tuple[Ubicacion, str]]:
    """Todos los errores por elemento: repetidas y ajenas al grupo."""
    candidatas = {m.inscripcion_id for m in entrada.asistencias if id_posible(m.inscripcion_id)}
    del_grupo = (
        set(
            sesion.execute(
                select(Inscripcion.id).where(
                    Inscripcion.id.in_(candidatas), Inscripcion.grupo_id == grupo_id
                )
            ).scalars()
        )
        if candidatas
        else set()
    )
    errores: list[tuple[Ubicacion, str]] = []
    vistas: set[int] = set()
    for indice, marca in enumerate(entrada.asistencias):
        ubicacion: Ubicacion = ("asistencias", indice, "inscripcion_id")
        if marca.inscripcion_id in vistas:
            errores.append((ubicacion, "Esa inscripción ya está en la lista."))
        elif marca.inscripcion_id not in del_grupo:
            errores.append((ubicacion, "Esa inscripción no es de este grupo."))
        vistas.add(marca.inscripcion_id)
    return errores


def guardar_asistencia(
    sesion: Session, usuario: Usuario, grupo_id: int, fecha: date, entrada: AsistenciaEntrada
) -> AsistenciaDelGrupo:
    """Guarda (o corrige) las marcas de la fecha y devuelve la lista completa.

    Levanta GrupoInexistente (404), TemporadaCerrada o GrupoInactivo (409),
    FechaFueraDeTemporada (422) o ReglaIncumplida (422, por elemento).
    """
    fila = (
        sesion.execute(
            select(
                Grupo.nombre,
                Grupo.turno,
                Grupo.activo,
                Temporada.estado,
                Temporada.fecha_inicio,
                Temporada.fecha_cierre,
            )
            .join(Temporada, Temporada.id == Grupo.temporada_id)
            .where(Grupo.id == grupo_id)
        ).one_or_none()
        if id_posible(grupo_id)
        else None
    )
    if fila is None:
        raise GrupoInexistente
    nombre, turno, activo, estado, inicio, cierre = fila
    if estado == EstadoTemporada.CERRADA:
        raise TemporadaCerrada
    if not activo:
        raise GrupoInactivo
    if not inicio <= fecha <= cierre:
        raise FechaFueraDeTemporada(inicio, cierre)
    errores = _errores_del_cuerpo(sesion, grupo_id, entrada)
    if errores:
        raise ReglaIncumplida(errores)

    # Un solo INSERT ... ON CONFLICT: atomico frente a dos pedidos a la vez.
    insercion = insert(Asistencia).values(
        [
            {
                "inscripcion_id": m.inscripcion_id,
                "fecha": fecha,
                "presente": m.presente,
                "registrado_por": usuario.id,
            }
            for m in entrada.asistencias
        ]
    )
    sesion.execute(
        insercion.on_conflict_do_update(
            constraint="uq_asistencia_inscripcion_fecha",
            set_={
                "presente": insercion.excluded.presente,
                "registrado_por": insercion.excluded.registrado_por,
                "registrado_en": func.now(),
            },
        )
    )
    sesion.commit()
    return _armar(sesion, grupo_id, nombre, turno, fecha)
