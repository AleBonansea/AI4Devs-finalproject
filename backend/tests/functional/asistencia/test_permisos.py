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
