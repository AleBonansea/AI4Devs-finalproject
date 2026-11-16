"""Capability `familias`: inscripciones de una familia (change cobro, tarea 3.4).

Un test por Scenario de `openspec/changes/cobro/specs/familias/spec.md`:
- Requirement «Inscripciones de una familia» (7 Scenarios).
- Requirement «Quién puede ver las inscripciones de una familia» (5 Scenarios).

Endpoint: `GET /api/v1/familias/{familia_id}/inscripciones`, solo Admin.

El estado se arma con los helpers de `asistencia/preparacion.py`: temporadas y
usuarios con el ORM, familias, alumnos, grupos e inscripciones con SQL crudo.
Los tokens salen del login real.

Al final del archivo hay un CONTROL POSITIVO que tiene que fallar.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    asignar,
    crear_alumno,
    crear_cerrada,
    crear_familia,
    crear_usuario,
    crear_vigente,
    ingresar,
    inscribir,
    insertar_grupo,
)

CAMPOS_DE_LA_INSCRIPCION = {"inscripcion_id", "alumno_id", "nombre", "apellido", "turno", "grupo"}
MENSAJE_FAMILIA_INEXISTENTE = "La familia no existe."
MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."
ID_INEXISTENTE = 999999
ID_FUERA_DE_RANGO = 9223372036854775808


def url_inscripciones(familia_id: int | str) -> str:
    return f"/api/v1/familias/{familia_id}/inscripciones"


def resumen(cuerpo: list[dict[str, Any]]) -> list[tuple[str, str, str, str]]:
    """(nombre, apellido, turno, grupo) de cada elemento, en el orden de la respuesta."""
    return [(e["nombre"], e["apellido"], e["turno"], e["grupo"]) for e in cuerpo]


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    return crear_vigente(sesion)


@pytest.fixture
def autor(sesion: Session) -> int:
    """Quien cargo las inscripciones: un Coordinador que no hace los pedidos."""
    return crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)


@pytest.fixture
def admin(cliente: TestClient, sesion: Session) -> dict[str, str]:
    crear_usuario(sesion, "admin1", RolUsuario.ADMIN)
    return ingresar(cliente, "admin1")


@pytest.fixture
def perez(sesion: Session) -> int:
    """La familia «Pérez – Ana»."""
    return crear_familia(sesion, "socio")


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    return insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def juan(sesion: Session, perez: int) -> int:
    return crear_alumno(sesion, "Juan", "Pérez", familia_id=perez)


@pytest.fixture
def juan_en_delfines(
    sesion: Session, vigente: int, autor: int, delfines_manana: int, juan: int
) -> int:
    return inscribir(sesion, juan, delfines_manana, vigente, "manana", autor)


# --- Requirement: Inscripciones de una familia -----------------------------


class TestInscripcionesDeUnaFamilia:
    def test_trae_las_tres_inscripciones_ordenadas_por_apellido_nombre_y_turno(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        autor: int,
        perez: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Hijos en uno y en los dos turnos
        # Datos elegidos para que el orden pedido no coincida con el de
        # insercion, ni con el de id, ni con el nombre del grupo: Juan se crea
        # antes que Ana, su inscripcion de la tarde antes que la de la manana,
        # y los grupos ordenados por nombre darian Delfines, Pulpos, Tiburones.
        pulpos = insertar_grupo(sesion, vigente, "Pulpos", "tarde")
        delfines = insertar_grupo(sesion, vigente, "Delfines", "manana")
        tiburones = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=perez)
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=perez)
        juan_tarde = inscribir(sesion, juan, pulpos, vigente, "tarde", autor)
        juan_manana = inscribir(sesion, juan, delfines, vigente, "manana", autor)
        ana_manana = inscribir(sesion, ana, tiburones, vigente, "manana", autor)

        respuesta = cliente.get(url_inscripciones(perez), headers=admin)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert resumen(cuerpo) == [
            ("Ana", "Pérez", "manana", "Tiburones"),
            ("Juan", "Pérez", "manana", "Delfines"),
            ("Juan", "Pérez", "tarde", "Pulpos"),
        ]
        assert [(e["inscripcion_id"], e["alumno_id"]) for e in cuerpo] == [
            (ana_manana, ana),
            (juan_manana, juan),
            (juan_tarde, juan),
        ]

    def test_trae_solo_las_inscripciones_de_la_temporada_vigente(
        self,
        cliente: TestClient,
        sesion: Session,
        autor: int,
        perez: int,
        juan_en_delfines: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Solo la temporada vigente
        cerrada = crear_cerrada(sesion)
        tiburones_viejo = insertar_grupo(sesion, cerrada, "Tiburones", "manana")
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=perez)
        inscribir(sesion, ana, tiburones_viejo, cerrada, "manana", autor)

        respuesta = cliente.get(url_inscripciones(perez), headers=admin)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert resumen(cuerpo) == [("Juan", "Pérez", "manana", "Delfines")]
        assert cuerpo[0]["inscripcion_id"] == juan_en_delfines

    def test_no_trae_a_los_alumnos_de_otra_familia(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        autor: int,
        perez: int,
        delfines_manana: int,
        juan_en_delfines: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Solo los hijos de esa familia
        gomez = crear_familia(sesion, "no_socio")
        lucia = crear_alumno(sesion, "Lucía", "Gómez", familia_id=gomez)
        inscribir(sesion, lucia, delfines_manana, vigente, "manana", autor)

        respuesta = cliente.get(url_inscripciones(perez), headers=admin)

        assert respuesta.status_code == 200, respuesta.text
        assert resumen(respuesta.json()) == [("Juan", "Pérez", "manana", "Delfines")]
        assert "Lucía" not in respuesta.text
        assert "Gómez" not in respuesta.text

    def test_una_familia_sin_inscripciones_en_la_temporada_da_lista_vacia(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        perez: int,
        juan: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Familia sin inscripciones en la temporada
        # Hay un grupo en la temporada vigente, pero Juan no esta inscripto.
        insertar_grupo(sesion, vigente, "Delfines", "manana")

        respuesta = cliente.get(url_inscripciones(perez), headers=admin)

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json() == []

    def test_cada_elemento_tiene_exactamente_los_seis_campos(
        self,
        cliente: TestClient,
        perez: int,
        juan_en_delfines: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Sin datos médicos ni de personas
        respuesta = cliente.get(url_inscripciones(perez), headers=admin)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert len(cuerpo) == 1
        for elemento in cuerpo:
            assert set(elemento) == CAMPOS_DE_LA_INSCRIPCION

    def test_una_familia_que_no_existe_da_404(
        self,
        cliente: TestClient,
        perez: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Familia que no existe
        assert perez != ID_INEXISTENTE

        respuesta = cliente.get(url_inscripciones(ID_INEXISTENTE), headers=admin)

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FAMILIA_INEXISTENTE

    def test_un_id_mas_grande_que_el_maximo_da_404(
        self,
        cliente: TestClient,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Id de familia más grande que el máximo
        respuesta = cliente.get(url_inscripciones(ID_FUERA_DE_RANGO), headers=admin)

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FAMILIA_INEXISTENTE


# --- Requirement: Quién puede ver las inscripciones de una familia ---------


class TestQuienPuedeVerLasInscripciones:
    def test_la_profesora_de_otro_grupo_recibe_403_sin_ningun_alumno(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        autor: int,
        perez: int,
        juan_en_delfines: int,
        admin: dict[str, str],
    ) -> None:
        # Scenario: Profesor de otro grupo
        # `cfernandez` esta asignada solo a «Pulpos» tarde, con Lucía Gómez y
        # sin ningun hijo de la familia Pérez.
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=perez)
        tiburones = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        inscribir(sesion, ana, tiburones, vigente, "manana", autor)
        pulpos = insertar_grupo(sesion, vigente, "Pulpos", "tarde")
        lucia = crear_alumno(sesion, "Lucía", "Gómez")
        inscribir(sesion, lucia, pulpos, vigente, "tarde", autor)
        cfernandez = crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        asignar(sesion, pulpos, cfernandez)

        respuesta = cliente.get(url_inscripciones(perez), headers=ingresar(cliente, "cfernandez"))

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        for texto in ("Ana", "Juan", "Pérez", "Tiburones", "Delfines"):
            assert texto not in respuesta.text

        # Contraste: el Admin con la misma familia si ve a los hijos, asi que
        # el 403 se debe al rol y no a una familia vacia.
        del_admin = cliente.get(url_inscripciones(perez), headers=admin)
        assert del_admin.status_code == 200, del_admin.text
        assert len(del_admin.json()) == 2

    def test_el_profesor_del_grupo_de_un_hijo_recibe_403(
        self,
        cliente: TestClient,
        sesion: Session,
        perez: int,
        delfines_manana: int,
        juan_en_delfines: int,
    ) -> None:
        # Scenario: Profesor del grupo de un hijo
        jperez = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, delfines_manana, jperez)

        respuesta = cliente.get(url_inscripciones(perez), headers=ingresar(cliente, "jperez"))

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        assert "Juan" not in respuesta.text

    def test_el_profesor_con_una_familia_que_no_existe_recibe_403_y_no_404(
        self,
        cliente: TestClient,
        sesion: Session,
        perez: int,
        delfines_manana: int,
    ) -> None:
        # Scenario: Profesor con una familia que no existe
        assert perez != ID_INEXISTENTE
        profesor = crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        asignar(sesion, delfines_manana, profesor)

        respuesta = cliente.get(
            url_inscripciones(ID_INEXISTENTE), headers=ingresar(cliente, "jperez")
        )

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO

    def test_el_coordinador_recibe_403(
        self,
        cliente: TestClient,
        sesion: Session,
        perez: int,
        juan_en_delfines: int,
    ) -> None:
        # Scenario: Coordinador
        crear_usuario(sesion, "mlopez", RolUsuario.COORDINADOR)

        respuesta = cliente.get(url_inscripciones(perez), headers=ingresar(cliente, "mlopez"))

        assert respuesta.status_code == 403, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_SIN_PERMISO
        assert "Juan" not in respuesta.text

    def test_sin_sesion_responde_401(
        self,
        cliente: TestClient,
        perez: int,
        juan_en_delfines: int,
    ) -> None:
        # Scenario: Sin sesión
        respuesta = cliente.get(url_inscripciones(perez))

        assert respuesta.status_code == 401, respuesta.text
        assert "Juan" not in respuesta.text
