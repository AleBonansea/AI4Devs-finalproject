"""Capability `asistencia`: las restricciones de la tabla `asistencia`.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «Un registro de asistencia por inscripcion y fecha».

Los endpoints todavia no existen, asi que el contrato que se prueba es el de
la base: cada test inserta con SQL crudo sobre las columnas fijadas en
`openspec/changes/asistencia/design.md` (seccion «Esquema») y comprueba que
Postgres guarde o rechace la fila. Temporada y usuario se crean con los
modelos que ya existen, igual que en `alumnos/test_alumnos_esquema.py`.

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


def _rechaza(sesion: Session, sql: str, parametros: Mapping[str, object]) -> IntegrityError:
    """La sentencia tiene que fallar en la base, aislada en un savepoint.

    Devuelve el error para que el test mire cual restriccion salto.
    """
    with pytest.raises(IntegrityError) as error, sesion.begin_nested():
        sesion.execute(text(sql), parametros)
    return error.value


def _contar(sesion: Session, sql: str, parametros: Mapping[str, object]) -> int:
    return int(sesion.execute(text(sql), parametros).scalar_one())


@pytest.fixture
def temporada_2026_27(sesion: Session) -> int:
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2027, 1, 4),
        fecha_cierre=date(2027, 2, 26),
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


def _crear_juan(sesion: Session) -> int:
    familia = int(
        sesion.execute(
            text("INSERT INTO familia (categoria) VALUES ('empleado') RETURNING id")
        ).scalar_one()
    )
    return int(
        sesion.execute(
            text(
                "INSERT INTO alumno (familia_id, nombre, apellido, fecha_nacimiento) "
                "VALUES (:f, 'Juan', 'Pérez', :n) RETURNING id"
            ),
            {"f": familia, "n": date(2020, 3, 10)},
        ).scalar_one()
    )


def _inscribir(
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


_INSERTAR_ASISTENCIA = (
    "INSERT INTO asistencia (inscripcion_id, fecha, presente, registrado_por) "
    "VALUES (:inscripcion_id, :fecha, :presente, :registrado_por)"
)


def _datos_asistencia(
    inscripcion_id: int, fecha: date, presente: bool | None, registrado_por: int
) -> dict[str, object]:
    return {
        "inscripcion_id": inscripcion_id,
        "fecha": fecha,
        "presente": presente,
        "registrado_por": registrado_por,
    }


def _registrar(
    sesion: Session, inscripcion_id: int, fecha: date, presente: bool, registrado_por: int
) -> None:
    sesion.execute(
        text(_INSERTAR_ASISTENCIA),
        _datos_asistencia(inscripcion_id, fecha, presente, registrado_por),
    )


def _registros_de(sesion: Session, inscripcion_id: int) -> list[tuple[date, bool]]:
    filas = sesion.execute(
        text("SELECT fecha, presente FROM asistencia " "WHERE inscripcion_id = :i ORDER BY fecha"),
        {"i": inscripcion_id},
    )
    return [(f[0], f[1]) for f in filas]


@pytest.fixture
def juan_en_delfines_manana(sesion: Session, temporada_2026_27: int, coordinador: int) -> int:
    """La inscripcion de Juan Perez en «Delfines» manana."""
    delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
    juan = _crear_juan(sesion)
    return _inscribir(sesion, juan, delfines_manana, temporada_2026_27, "manana", coordinador)


# --- Requirement: Un registro de asistencia por inscripcion y fecha --------


class TestUnRegistroPorInscripcionYFecha:
    def test_la_base_rechaza_un_segundo_registro_para_la_misma_inscripcion_y_fecha(
        self, sesion: Session, juan_en_delfines_manana: int, coordinador: int
    ) -> None:
        # Scenario: Dos registros para la misma inscripcion y fecha
        _registrar(sesion, juan_en_delfines_manana, date(2027, 1, 5), True, coordinador)

        error = _rechaza(
            sesion,
            _INSERTAR_ASISTENCIA,
            _datos_asistencia(juan_en_delfines_manana, date(2027, 1, 5), False, coordinador),
        )

        assert error.orig is not None
        assert error.orig.diag.constraint_name == "uq_asistencia_inscripcion_fecha"  # type: ignore[union-attr]
        # El primer registro sigue tal cual y no aparecio otro.
        assert _registros_de(sesion, juan_en_delfines_manana) == [(date(2027, 1, 5), True)]

    def test_un_registro_de_la_misma_inscripcion_en_otra_fecha_queda_guardado(
        self, sesion: Session, juan_en_delfines_manana: int, coordinador: int
    ) -> None:
        # Scenario: La misma inscripcion en otra fecha
        _registrar(sesion, juan_en_delfines_manana, date(2027, 1, 5), True, coordinador)

        _registrar(sesion, juan_en_delfines_manana, date(2027, 1, 6), False, coordinador)

        assert _registros_de(sesion, juan_en_delfines_manana) == [
            (date(2027, 1, 5), True),
            (date(2027, 1, 6), False),
        ]

    def test_un_registro_del_mismo_alumno_y_fecha_en_el_otro_turno_queda_guardado(
        self, sesion: Session, temporada_2026_27: int, coordinador: int
    ) -> None:
        # Scenario: El mismo alumno y fecha en el otro turno
        delfines_manana = _crear_grupo(sesion, temporada_2026_27, "Delfines", "manana")
        pulpos_tarde = _crear_grupo(sesion, temporada_2026_27, "Pulpos", "tarde")
        juan = _crear_juan(sesion)
        manana = _inscribir(sesion, juan, delfines_manana, temporada_2026_27, "manana", coordinador)
        tarde = _inscribir(sesion, juan, pulpos_tarde, temporada_2026_27, "tarde", coordinador)
        _registrar(sesion, manana, date(2027, 1, 5), True, coordinador)

        _registrar(sesion, tarde, date(2027, 1, 5), False, coordinador)

        assert _registros_de(sesion, manana) == [(date(2027, 1, 5), True)]
        assert _registros_de(sesion, tarde) == [(date(2027, 1, 5), False)]

    def test_la_base_rechaza_un_registro_sin_presente(
        self, sesion: Session, juan_en_delfines_manana: int, coordinador: int
    ) -> None:
        # Scenario: Registro sin presente
        # Se mandan todas las demas columnas obligatorias, para que lo unico
        # que falte sea `presente`. Va el INSERT sin la columna, no con NULL
        # explicito: asi tambien se comprueba que no tenga un default.
        error = _rechaza(
            sesion,
            "INSERT INTO asistencia (inscripcion_id, fecha, registrado_por) "
            "VALUES (:inscripcion_id, :fecha, :registrado_por)",
            {
                "inscripcion_id": juan_en_delfines_manana,
                "fecha": date(2027, 1, 5),
                "registrado_por": coordinador,
            },
        )

        assert error.orig is not None
        # 23502 es not_null_violation; la columna que salto es `presente`.
        assert error.orig.sqlstate == "23502"  # type: ignore[union-attr]
        assert error.orig.diag.column_name == "presente"  # type: ignore[union-attr]
        assert _registros_de(sesion, juan_en_delfines_manana) == []
