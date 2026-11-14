"""Capability `asistencia`: quien puede abrir y guardar la asistencia.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «Quién puede abrir y guardar la asistencia».

En esta tarea van solo los Scenarios del `GET`: «Profesor en su grupo»,
«Profesor abre un grupo ajeno», «Profesor con un grupo que no existe» y
«Admin en cualquier grupo». Los del `PUT` (Profesor guarda en un grupo
ajeno, grupo ajeno de una temporada cerrada, Coordinador sin grupos, sin
sesion) se suman a la misma clase en la tarea siguiente.

Estado comun: `jperez` es Profesor asignado solo a «Delfines» manana, con
Juan Perez inscripto; Lucia Gomez esta inscripta en «Pulpos» tarde, que tiene
su propio profesor (no es un grupo sin duenio).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    MENSAJE_GRUPO_AJENO,
    asignar,
    crear_alumno,
    crear_usuario,
    crear_vigente,
    ingresar,
    inscribir,
    insertar_grupo,
    nombres_y_presente,
    url_asistencia,
)

# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    return crear_vigente(sesion)


@pytest.fixture
def autor(sesion: Session) -> int:
    """Quien cargo las inscripciones: un Coordinador que no participa del pedido."""
    return crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    return insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def juan_en_delfines(sesion: Session, vigente: int, delfines_manana: int, autor: int) -> int:
    juan = crear_alumno(sesion, "Juan", "Pérez")
    return inscribir(sesion, juan, delfines_manana, vigente, "manana", autor)


@pytest.fixture
def pulpos_tarde(sesion: Session, vigente: int) -> int:
    grupo = insertar_grupo(sesion, vigente, "Pulpos", "tarde")
    otro_profesor = crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
    asignar(sesion, grupo, otro_profesor)
    return grupo


@pytest.fixture
def lucia_en_pulpos(sesion: Session, vigente: int, pulpos_tarde: int, autor: int) -> int:
    lucia = crear_alumno(sesion, "Lucía", "Gómez")
    return inscribir(sesion, lucia, pulpos_tarde, vigente, "tarde", autor)


@pytest.fixture
def jperez(cliente: TestClient, sesion: Session, delfines_manana: int) -> dict[str, str]:
    """Profesor asignado solo a «Delfines» manana."""
    profesor = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
    asignar(sesion, delfines_manana, profesor)
    return ingresar(cliente, "jperez")


# --- Requirement: Quién puede abrir y guardar la asistencia ----------------


class TestQuienPuedeAbrirYGuardar:
    def test_el_profesor_abre_su_grupo_y_ve_a_juan(
        self,
        cliente: TestClient,
        delfines_manana: int,
        juan_en_delfines: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor en su grupo
        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=jperez)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == delfines_manana
        assert nombres_y_presente(cuerpo) == [("Juan", "Pérez", None)]
        assert cuerpo["alumnos"][0]["inscripcion_id"] == juan_en_delfines

    def test_el_profesor_en_un_grupo_ajeno_recibe_403_sin_datos_de_lucia(
        self,
        cliente: TestClient,
        delfines_manana: int,
        juan_en_delfines: int,
        pulpos_tarde: int,
        lucia_en_pulpos: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor abre un grupo ajeno
        respuesta = cliente.get(url_asistencia(pulpos_tarde, "2027-01-05"), headers=jperez)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert "Lucía" not in respuesta.text
        assert "Gómez" not in respuesta.text

        # Contraste: el mismo pedido sobre su grupo responde 200, asi que el
        # 403 se debe al grupo y no a la sesion.
        en_su_grupo = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=jperez)
        assert en_su_grupo.status_code == 200, en_su_grupo.text

    def test_el_profesor_con_un_grupo_que_no_existe_recibe_403(
        self,
        cliente: TestClient,
        delfines_manana: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor con un grupo que no existe
        assert delfines_manana != 999999

        respuesta = cliente.get(url_asistencia(999999, "2027-01-05"), headers=jperez)

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO

    def test_el_admin_sin_grupos_abre_un_grupo_cualquiera_y_ve_a_lucia(
        self,
        cliente: TestClient,
        sesion: Session,
        pulpos_tarde: int,
        lucia_en_pulpos: int,
    ) -> None:
        # Scenario: Admin en cualquier grupo
        crear_usuario(sesion, "admin1", RolUsuario.ADMIN)

        respuesta = cliente.get(
            url_asistencia(pulpos_tarde, "2027-01-05"), headers=ingresar(cliente, "admin1")
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == pulpos_tarde
        assert nombres_y_presente(cuerpo) == [("Lucía", "Gómez", None)]
        assert cuerpo["alumnos"][0]["inscripcion_id"] == lucia_en_pulpos


# --- Requirement: Quién puede abrir y guardar la asistencia (PUT) ----------
# Tarea 2.2. Clase aparte e imports aca abajo para no tocar lo que ya estaba.

from datetime import date  # noqa: E402

from tests.functional.asistencia.preparacion import (  # noqa: E402
    contar_asistencias,
    crear_cerrada,
    cuerpo_guardado,
    registros_de,
)


class TestQuienPuedeGuardar:
    def test_el_profesor_guarda_en_un_grupo_ajeno_y_recibe_403_sin_guardar(
        self,
        cliente: TestClient,
        sesion: Session,
        juan_en_delfines: int,
        pulpos_tarde: int,
        lucia_en_pulpos: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor guarda en un grupo ajeno
        respuesta = cliente.put(
            url_asistencia(pulpos_tarde, "2027-01-05"),
            json=cuerpo_guardado((lucia_en_pulpos, True)),
            headers=jperez,
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert "Lucía" not in respuesta.text
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0

    def test_el_profesor_con_un_grupo_ajeno_cerrado_y_fecha_fuera_recibe_403(
        self,
        cliente: TestClient,
        sesion: Session,
        autor: int,
        juan_en_delfines: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor con un grupo ajeno de una temporada cerrada y
        # fecha fuera de ella
        # Cuerpo valido para ese grupo: el permiso tiene que decidir antes
        # que la temporada cerrada (409) y la fecha fuera de rango (422).
        cerrada = crear_cerrada(sesion)
        grupo_viejo = insertar_grupo(sesion, cerrada, "Delfines", "manana")
        lucia = crear_alumno(sesion, "Lucía", "Gómez")
        inscripcion = inscribir(sesion, lucia, grupo_viejo, cerrada, "manana", autor)

        respuesta = cliente.put(
            url_asistencia(grupo_viejo, "2027-01-05"),
            json=cuerpo_guardado((inscripcion, True)),
            headers=jperez,
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_AJENO
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0

    def test_el_coordinador_sin_grupos_guarda_y_queda_como_autor(
        self,
        cliente: TestClient,
        sesion: Session,
        pulpos_tarde: int,
        lucia_en_pulpos: int,
    ) -> None:
        # Scenario: Coordinador sin grupos asignados
        # Un Coordinador distinto de `autor`, el que cargo las inscripciones:
        # asi el autor del registro no coincide con nadie por casualidad.
        mlopez = crear_usuario(sesion, "mlopez", RolUsuario.COORDINADOR)

        respuesta = cliente.put(
            url_asistencia(pulpos_tarde, "2027-01-05"),
            json=cuerpo_guardado((lucia_en_pulpos, True)),
            headers=ingresar(cliente, "mlopez"),
        )

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [("Lucía", "Gómez", True)]
        registros = registros_de(sesion, lucia_en_pulpos, date(2027, 1, 5))
        assert [(r.presente, r.registrado_por) for r in registros] == [(True, mlopez)]

    def test_sin_sesion_responde_401_y_no_guarda(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        juan_en_delfines: int,
    ) -> None:
        # Scenario: Sin sesión
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan_en_delfines, True)),
        )

        assert respuesta.status_code == 401, respuesta.text
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0


# --- Requirement: Quién puede abrir y guardar la asistencia (tarea 7.3) ----

from tests.functional.asistencia.preparacion import errores_con_loc_terminado_en  # noqa: E402


class TestProfesorNoCuelaInscripcionesAjenas:
    def test_el_profesor_que_cuela_una_inscripcion_de_otro_grupo_recibe_422_sin_guardar(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        autor: int,
        delfines_manana: int,
        juan_en_delfines: int,
        jperez: dict[str, str],
    ) -> None:
        # Scenario: Profesor cuela en su grupo una inscripción de otro grupo
        tiburones = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        ana = crear_alumno(sesion, "Ana", "Pérez")
        ana_en_tiburones = inscribir(sesion, ana, tiburones, vigente, "manana", autor)

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan_en_delfines, True), (ana_en_tiburones, True)),
            headers=jperez,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias", 1, "inscripcion_id")
        assert [e["msg"] for e in errores] == [
            "Esa inscripción no es de este grupo."
        ], respuesta.text
        assert not errores_con_loc_terminado_en(respuesta, "asistencias", 0, "inscripcion_id")
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0
