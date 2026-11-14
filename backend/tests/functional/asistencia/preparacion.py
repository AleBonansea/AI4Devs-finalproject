"""Preparacion compartida de los tests de los endpoints de asistencia.

No es un archivo de tests (pytest no lo junta: no empieza con `test_`). Lo
usan `test_abrir.py`, `test_fecha.py`, `test_grupos_sin_guardado.py` y
`test_permisos.py`, y lo van a usar los Scenarios del `PUT`.

El estado se arma igual que en `alumnos/test_alta.py` y `grupos/`: las
temporadas y los usuarios con el ORM, el resto con SQL crudo sobre los
nombres del modelo de datos. Los tokens salen del login real.

Como el `PUT` todavia no existe, la asistencia «ya registrada» se inserta
directo en la tabla `asistencia`.

Fechas de las temporadas, las de la spec:
- vigente 2026-27: del 2027-01-04 al 2027-02-26;
- cerrada 2025-26: del 2026-01-05 al 2026-02-27.
"""

from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
CONTRASENA = "Verano2026"

CAMPOS_DEL_ALUMNO = {"inscripcion_id", "nombre", "apellido", "presente"}
MENSAJE_GRUPO_AJENO = "Solo podés tomar asistencia de tus grupos."
MENSAJE_GRUPO_INEXISTENTE = "El grupo no existe."
MENSAJE_FUERA_DE_TEMPORADA_VIGENTE = (
    "La fecha está fuera de la temporada del grupo, del 04/01/2027 al 26/02/2027."
)

INICIO_VIGENTE = date(2027, 1, 4)
CIERRE_VIGENTE = date(2027, 2, 26)
INICIO_CERRADA = date(2026, 1, 5)
CIERRE_CERRADA = date(2026, 2, 27)


def url_asistencia(grupo_id: int | str, fecha: str) -> str:
    return f"/api/v1/grupos/{grupo_id}/asistencias/{fecha}"


# --- temporadas, usuarios y sesion ------------------------------------------


def crear_temporada(
    sesion: Session, nombre: str, estado: EstadoTemporada, inicio: date, cierre: date
) -> int:
    temporada = Temporada(nombre=nombre, fecha_inicio=inicio, fecha_cierre=cierre, estado=estado)
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def crear_vigente(sesion: Session) -> int:
    return crear_temporada(
        sesion, "2026-27", EstadoTemporada.VIGENTE, INICIO_VIGENTE, CIERRE_VIGENTE
    )


def crear_cerrada(sesion: Session) -> int:
    return crear_temporada(
        sesion, "2025-26", EstadoTemporada.CERRADA, INICIO_CERRADA, CIERRE_CERRADA
    )


def crear_usuario(sesion: Session, username: str, rol: RolUsuario) -> int:
    # Nombre y apellido del usuario a proposito distintos de los de los
    # alumnos: el test del grupo ajeno busca «Gómez» en el texto crudo.
    usuario = Usuario(
        username=username,
        password_hash=hashear(CONTRASENA),
        debe_cambiar_password=False,
        intentos_fallidos=0,
        nombre="Usuario",
        apellido=username.capitalize(),
        rol=rol,
        activo=True,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario.id


def ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


# --- grupos, alumnos e inscripciones ----------------------------------------


def insertar_grupo(
    sesion: Session, temporada_id: int, nombre: str, turno: str, *, activo: bool = True
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, :n, :tu, :d, :h, :a) RETURNING id"
            ),
            {
                "t": temporada_id,
                "n": nombre,
                "tu": turno,
                "d": date(2017, 1, 1),
                "h": date(2021, 12, 31),
                "a": activo,
            },
        ).scalar_one()
    )


def asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def crear_familia(sesion: Session, categoria: str = "empleado") -> int:
    return int(
        sesion.execute(
            text("INSERT INTO familia (categoria) VALUES (:c) RETURNING id"), {"c": categoria}
        ).scalar_one()
    )


def crear_alumno(
    sesion: Session,
    nombre: str,
    apellido: str,
    *,
    familia_id: int | None = None,
    nacimiento: date = date(2019, 3, 10),
) -> int:
    familia = familia_id if familia_id is not None else crear_familia(sesion)
    return int(
        sesion.execute(
            text(
                "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
                "VALUES (:f, :n, :a, :fn) RETURNING id"
            ),
            {"f": familia, "n": nombre, "a": apellido, "fn": nacimiento},
        ).scalar_one()
    )


def inscribir(
    sesion: Session,
    alumno_id: int,
    grupo_id: int,
    temporada_id: int,
    turno: str,
    creado_por: int,
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO inscripcion "
                "(alumno_id, grupo_id, temporada_id, turno, creado_por) "
                "VALUES (:a, :g, :t, :tu, :c) RETURNING id"
            ),
            {"a": alumno_id, "g": grupo_id, "t": temporada_id, "tu": turno, "c": creado_por},
        ).scalar_one()
    )


def registrar_asistencia(
    sesion: Session, inscripcion_id: int, fecha: date, presente: bool, registrado_por: int
) -> None:
    """Asistencia «ya registrada», insertada directo en la base."""
    sesion.execute(
        text(
            "INSERT INTO asistencia (inscripcion_id, fecha, presente, registrado_por) "
            "VALUES (:i, :f, :p, :r)"
        ),
        {"i": inscripcion_id, "f": fecha, "p": presente, "r": registrado_por},
    )


def contar_asistencias(sesion: Session, fecha: date | None = None) -> int:
    if fecha is None:
        return int(sesion.execute(text("SELECT count(*) FROM asistencia")).scalar_one())
    return int(
        sesion.execute(
            text("SELECT count(*) FROM asistencia WHERE fecha = :f"), {"f": fecha}
        ).scalar_one()
    )


# --- lectura de la respuesta ------------------------------------------------


def nombres_y_presente(cuerpo: dict[str, Any]) -> list[tuple[str, str, bool | None]]:
    """(nombre, apellido, presente) de cada alumno, en el orden de la respuesta."""
    return [(a["nombre"], a["apellido"], a["presente"]) for a in cuerpo["alumnos"]]


def errores_con_loc_terminado_en(respuesta: Any, *final: str | int) -> list[dict[str, Any]]:
    """Los errores de `detail` cuyo `loc` termina en `final`."""
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    largo = len(final)
    return [e for e in detalle if list(e["loc"])[-largo:] == list(final)]
