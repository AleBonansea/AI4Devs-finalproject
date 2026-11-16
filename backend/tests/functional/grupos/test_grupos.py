"""Capability `grupos`: las restricciones de `grupo` y `grupo_profesor`.

Un test por Scenario de
`openspec/changes/tarifario-y-semilla/specs/grupos/spec.md`.

Este change no expone nada por la API, asi que el contrato que se prueba es
el de la base: cada test inserta con SQL crudo sobre los nombres de
`3-modelo-de-datos.md` y comprueba que Postgres guarde o rechace la fila. El
SQL crudo es a proposito: el ORM rechazaria un turno inexistente antes de
llegar a la base, y el Scenario dice que la rechaza la base.

Cada insercion rechazada va dentro de `sesion.begin_nested()`: si no, el
error aborta la transaccion y lo que se comprueba despues no corre.
"""

from collections.abc import Mapping
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

# --- preparacion -----------------------------------------------------------


def _crear_temporada(sesion: Session, nombre: str, estado: EstadoTemporada) -> int:
    temporada = Temporada(
        nombre=nombre,
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=estado,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def _crear_profesor(sesion: Session, username: str) -> int:
    usuario = Usuario(
        username=username,
        password_hash="$argon2id$no-es-un-hash-real",
        nombre="Juan",
        apellido="Perez",
        rol=RolUsuario.PROFESOR,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario.id


@pytest.fixture
def temporada_2026_27(sesion: Session) -> int:
    return _crear_temporada(sesion, "2026-27", EstadoTemporada.VIGENTE)


_INSERTAR_GRUPO = (
    "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, nacimiento_hasta) "
    "VALUES (:temporada_id, :nombre, :turno, :desde, :hasta) RETURNING id"
)


def _datos_grupo(temporada_id: int, **extra: object) -> dict[str, object]:
    datos: dict[str, object] = {
        "temporada_id": temporada_id,
        "nombre": "Delfines",
        "turno": "manana",
        "desde": date(2019, 1, 1),
        "hasta": date(2019, 12, 31),
    }
    datos.update(extra)
    return datos


def _insertar_grupo(sesion: Session, temporada_id: int, **extra: object) -> int:
    return int(
        sesion.execute(text(_INSERTAR_GRUPO), _datos_grupo(temporada_id, **extra)).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


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


def _grupos_llamados(sesion: Session, temporada_id: int, nombre: str, turno: str) -> int:
    return _contar(
        sesion,
        "SELECT count(*) FROM grupo WHERE temporada_id = :t AND nombre = :n AND turno = :tu",
        {"t": temporada_id, "n": nombre, "tu": turno},
    )


# --- Requirement: Un grupo pertenece a una temporada y a un turno ----------


class TestGrupoPorTemporadaYTurno:
    def test_la_base_rechaza_mismo_nombre_y_turno_en_la_misma_temporada(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Mismo nombre y turno en la misma temporada
        _insertar_grupo(sesion, temporada_2026_27, nombre="Delfines", turno="manana")
        _rechaza(
            sesion,
            _INSERTAR_GRUPO,
            _datos_grupo(temporada_2026_27, nombre="Delfines", turno="manana"),
        )
        assert _grupos_llamados(sesion, temporada_2026_27, "Delfines", "manana") == 1

    def test_el_mismo_nombre_en_el_otro_turno_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Mismo nombre en el otro turno
        _insertar_grupo(sesion, temporada_2026_27, nombre="Delfines", turno="manana")
        _insertar_grupo(sesion, temporada_2026_27, nombre="Delfines", turno="tarde")
        assert _grupos_llamados(sesion, temporada_2026_27, "Delfines", "manana") == 1
        assert _grupos_llamados(sesion, temporada_2026_27, "Delfines", "tarde") == 1

    def test_el_mismo_nombre_y_turno_en_otra_temporada_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Mismo nombre y turno en otra temporada
        temporada_2025_26 = _crear_temporada(sesion, "2025-26", EstadoTemporada.CERRADA)
        _insertar_grupo(sesion, temporada_2025_26, nombre="Delfines", turno="manana")
        _insertar_grupo(sesion, temporada_2026_27, nombre="Delfines", turno="manana")
        assert _grupos_llamados(sesion, temporada_2025_26, "Delfines", "manana") == 1
        assert _grupos_llamados(sesion, temporada_2026_27, "Delfines", "manana") == 1

    def test_la_base_rechaza_un_turno_que_no_existe(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Un turno que no existe
        _rechaza(
            sesion,
            _INSERTAR_GRUPO,
            _datos_grupo(temporada_2026_27, turno="noche"),
            errores=(DataError, IntegrityError),
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM grupo WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )


# --- Requirement: Rango de fechas de nacimiento del grupo ------------------


class TestRangoDeNacimiento:
    def test_un_rango_de_un_solo_dia_queda_guardado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Rango de un solo dia (limite de adentro)
        grupo_id = _insertar_grupo(
            sesion, temporada_2026_27, desde=date(2019, 1, 1), hasta=date(2019, 1, 1)
        )
        fila = sesion.execute(
            text("SELECT nacimiento_desde, nacimiento_hasta FROM grupo WHERE id = :id"),
            {"id": grupo_id},
        ).one()
        assert fila[0] == date(2019, 1, 1)
        assert fila[1] == date(2019, 1, 1)

    def test_la_base_rechaza_un_rango_invertido_por_un_dia(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Rango invertido por un dia (limite de afuera)
        _rechaza(
            sesion,
            _INSERTAR_GRUPO,
            _datos_grupo(temporada_2026_27, desde=date(2019, 1, 2), hasta=date(2019, 1, 1)),
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM grupo WHERE temporada_id = :t",
                {"t": temporada_2026_27},
            )
            == 0
        )


# --- Requirement: Un grupo nuevo esta activo -------------------------------


class TestGrupoActivo:
    def test_un_grupo_creado_sin_indicar_activo_queda_activo(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Grupo creado sin indicar si esta activo
        grupo_id = _insertar_grupo(sesion, temporada_2026_27)
        activo = sesion.execute(
            text("SELECT activo FROM grupo WHERE id = :id"), {"id": grupo_id}
        ).scalar_one()
        assert activo is True


# --- Requirement: Profesores asignados a un grupo --------------------------


class TestProfesoresAsignados:
    def test_un_profesor_queda_asignado_a_dos_grupos_de_distinto_turno(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Un profesor en dos grupos de distinto turno
        jperez = _crear_profesor(sesion, "jperez")
        manana = _insertar_grupo(sesion, temporada_2026_27, turno="manana")
        tarde = _insertar_grupo(sesion, temporada_2026_27, turno="tarde")
        _asignar(sesion, manana, jperez)
        _asignar(sesion, tarde, jperez)
        grupos = {
            f[0]
            for f in sesion.execute(
                text("SELECT grupo_id FROM grupo_profesor WHERE usuario_id = :u"),
                {"u": jperez},
            )
        }
        assert grupos == {manana, tarde}

    def test_dos_profesores_quedan_asignados_al_mismo_grupo(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Dos profesores en el mismo grupo
        jperez = _crear_profesor(sesion, "jperez")
        cfernandez = _crear_profesor(sesion, "cfernandez")
        grupo = _insertar_grupo(sesion, temporada_2026_27, turno="manana")
        _asignar(sesion, grupo, jperez)
        _asignar(sesion, grupo, cfernandez)
        profesores = {
            f[0]
            for f in sesion.execute(
                text("SELECT usuario_id FROM grupo_profesor WHERE grupo_id = :g"),
                {"g": grupo},
            )
        }
        assert profesores == {jperez, cfernandez}

    def test_la_base_rechaza_la_misma_asignacion_dos_veces(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: La misma asignacion dos veces
        jperez = _crear_profesor(sesion, "jperez")
        grupo = _insertar_grupo(sesion, temporada_2026_27, turno="manana")
        _asignar(sesion, grupo, jperez)
        _rechaza(
            sesion,
            "INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)",
            {"g": grupo, "u": jperez},
        )
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM grupo_profesor WHERE grupo_id = :g AND usuario_id = :u",
                {"g": grupo, "u": jperez},
            )
            == 1
        )


# --- Requirement: Un grupo con profesores no se borra en cascada -----------


class TestSinBorradoEnCascada:
    def test_la_base_rechaza_borrar_un_grupo_con_un_profesor_asignado(
        self, sesion: Session, temporada_2026_27: int
    ) -> None:
        # Scenario: Borrar un grupo con un profesor asignado
        jperez = _crear_profesor(sesion, "jperez")
        grupo = _insertar_grupo(sesion, temporada_2026_27, turno="manana")
        _asignar(sesion, grupo, jperez)

        _rechaza(sesion, "DELETE FROM grupo WHERE id = :id", {"id": grupo})

        # AND el grupo y la asignacion siguen en la base
        assert _contar(sesion, "SELECT count(*) FROM grupo WHERE id = :id", {"id": grupo}) == 1
        assert (
            _contar(
                sesion,
                "SELECT count(*) FROM grupo_profesor WHERE grupo_id = :g AND usuario_id = :u",
                {"g": grupo, "u": jperez},
            )
            == 1
        )
