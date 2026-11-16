"""Capability `alumnos`: las restricciones de `alumno` e `inscripcion`.

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/alumnos/spec.md`, Requirements
«Ficha minima del alumno» e «Inscripcion en un grupo y turno».

Esta tarea no expone nada por la API, asi que el contrato que se prueba es el
de la base: cada test inserta con SQL crudo sobre los nombres de
`3-modelo-de-datos.md` y comprueba que Postgres guarde o rechace la fila.
Temporada y usuario se crean con los modelos que ya existen, igual que en
`grupos/test_grupos.py`.

Cada sentencia rechazada va dentro de `sesion.begin_nested()`: si no, el
error aborta la transaccion y lo que se comprueba despues no corre.
"""

from collections.abc import Mapping
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

# --- preparacion -----------------------------------------------------------


def _rechaza(
    sesion: Session,
    sql: str,
    parametros: Mapping[str, object],
    errores: type[Exception] | tuple[type[Exception], ...] = IntegrityError,
) -> None:
    """La sentencia tiene que fallar en la base, aislada en un savepoint."""
    with pytest.raises(errores), sesion.begin_nested():
        sesion.execute(text(sql), parametros)


def _contar(sesion: Session, sql: str, parametros: Mapping[str, object]) -> int:
    return int(sesion.execute(text(sql), parametros).scalar_one())


@pytest.fixture
def temporada_2026_27(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


@pytest.fixture
def coordinador(sesion: Session) -> int:
    usuario = Usuario(
        username="coordinadora",
        password_hash="$argon2id$no-es-un-hash-real",
        nombre="Carla",
        apellido="Fernandez",
        rol=RolUsuario.COORDINADOR,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario.id


def _crear_grupo(sesion: Session, temporada_id: int, nombre: str, turno: str) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo "
                "(temporada_id, nombre, turno, nacimiento_desde, nacimiento_hasta) "
                "VALUES (:t, :n, :tu, :d, :h) RETURNING id"
            ),
            {
                "t": temporada_id,
                "n": nombre,
                "tu": turno,
                "d": date(2017, 1, 1),
                "h": date(2021, 12, 31),
            },
        ).scalar_one()
    )


def _crear_familia(sesion: Session) -> int:
    return int(
        sesion.execute(
            text("INSERT INTO familia (categoria) VALUES ('empleado') RETURNING id")
        ).scalar_one()
    )


_INSERTAR_ALUMNO = (
    "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
    "VALUES (:familia_id, :nombre, :apellido, :fecha_nacimiento) RETURNING id"
)


def _crear_juan(sesion: Session) -> int:
    familia = _crear_familia(sesion)
    return int(
        sesion.execute(
            text(_INSERTAR_ALUMNO),
            {
                "familia_id": familia,
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": date(2020, 3, 10),
            },
        ).scalar_one()
    )


_INSERTAR_INSCRIPCION = (
    "INSERT INTO inscripcion (alumno_id, grupo_id, temporada_id, turno, creado_por) "
    "VALUES (:alumno_id, :grupo_id, :temporada_id, :turno, :creado_por)"
)


def _datos_inscripcion(
    alumno_id: int, grupo_id: int, temporada_id: int, turno: str, creado_por: int
) -> dict[str, object]:
    return {
        "alumno_id": alumno_id,
        "grupo_id": grupo_id,
        "temporada_id": temporada_id,
        "turno": turno,
        "creado_por": creado_por,
    }


def _inscribir(
    sesion: Session,
    alumno_id: int,
    grupo_id: int,
    temporada_id: int,
    turno: str,
    creado_por: int,
) -> None:
    sesion.execute(
        text(_INSERTAR_INSCRIPCION),
        _datos_inscripcion(alumno_id, grupo_id, temporada_id, turno, creado_por),
    )


def _inscripciones_de(sesion: Session, alumno_id: int) -> int:
    return _contar(
        sesion,
        "SELECT count(*) FROM inscripcion WHERE alumno_id = :a",
        {"a": alumno_id},
    )


# --- Requirement: Ficha minima del alumno ----------------------------------


class TestFichaMinima:
    def test_la_base_rechaza_un_alumno_sin_familia(self, sesion: Session) -> None:
        # Scenario: Alumno sin familia
        antes = _contar(sesion, "SELECT count(*) FROM alumno", {})
        _rechaza(
            sesion,
            _INSERTAR_ALUMNO,
            {
                "familia_id": None,
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": date(2020, 3, 10),
            },
        )
        assert _contar(sesion, "SELECT count(*) FROM alumno", {}) == antes

    def test_la_base_rechaza_un_alumno_sin_fecha_de_nacimiento(self, sesion: Session) -> None:
        # Scenario: Alumno sin fecha de nacimiento
        familia = _crear_familia(sesion)
        _rechaza(
            sesion,
            _INSERTAR_ALUMNO,
            {
                "familia_id": familia,
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": None,
            },
        )
        assert (
            _contar(sesion, "SELECT count(*) FROM alumno WHERE familia_id = :f", {"f": familia})
            == 0
        )


# --- Requirement: Inscripcion en un grupo y turno --------------------------


class TestInscripcion:
    def test_la_base_rechaza_una_segunda_inscripcion_en_el_mismo_turno_y_temporada(
        self, sesion: Session, temporada_2026_27: int, coordinador: int
    ) -> None:
        # Scenario: Segunda inscripcion en el mismo turno y temporada
        delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
        tiburones_manana = _crear_grupo(sesion, temporada_2026_27, "Tiburones", "manana")
        juan = _crear_juan(sesion)
        _inscribir(sesion, juan, delfines_manana, temporada_2026_27, "manana", coordinador)

        _rechaza(
            sesion,
            _INSERTAR_INSCRIPCION,
            _datos_inscripcion(juan, tiburones_manana, temporada_2026_27, "manana", coordinador),
        )
        assert _inscripciones_de(sesion, juan) == 1

    def test_una_inscripcion_en_el_otro_turno_queda_guardada(
        self, sesion: Session, temporada_2026_27: int, coordinador: int
    ) -> None:
        # Scenario: Inscripcion en el otro turno
        delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
        delfines_tarde = _crear_grupo(sesion, temporada_2026_27, "Delfines", "tarde")
        juan = _crear_juan(sesion)
        _inscribir(sesion, juan, delfines_manana, temporada_2026_27, "manana", coordinador)

        _inscribir(sesion, juan, delfines_tarde, temporada_2026_27, "tarde", coordinador)

        grupos = {
            f[0]
            for f in sesion.execute(
                text("SELECT grupo_id FROM inscripcion WHERE alumno_id = :a"), {"a": juan}
            )
        }
        assert grupos == {delfines_manana, delfines_tarde}

    def test_la_base_rechaza_una_inscripcion_con_turno_distinto_del_de_su_grupo(
        self, sesion: Session, temporada_2026_27: int, coordinador: int
    ) -> None:
        # Scenario: Turno distinto del de su grupo
        delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
        juan = _crear_juan(sesion)
        _rechaza(
            sesion,
            _INSERTAR_INSCRIPCION,
            _datos_inscripcion(juan, delfines_manana, temporada_2026_27, "tarde", coordinador),
        )
        assert _inscripciones_de(sesion, juan) == 0

    def test_la_base_rechaza_borrar_un_alumno_inscripto_y_la_inscripcion_sigue(
        self, sesion: Session, temporada_2026_27: int, coordinador: int
    ) -> None:
        # Scenario: Borrar un alumno inscripto
        delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
        juan = _crear_juan(sesion)
        _inscribir(sesion, juan, delfines_manana, temporada_2026_27, "manana", coordinador)

        _rechaza(sesion, "DELETE FROM alumno WHERE id = :id", {"id": juan})

        # AND la inscripcion sigue en la base
        assert _contar(sesion, "SELECT count(*) FROM alumno WHERE id = :id", {"id": juan}) == 1
        assert _inscripciones_de(sesion, juan) == 1
