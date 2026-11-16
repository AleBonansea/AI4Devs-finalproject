"""Capability `asistencia`: el cuerpo del guardado.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «El cuerpo del guardado» (`PUT
/api/v1/grupos/{grupo_id}/asistencias/{fecha}`).

Cada rechazo es 422 y no guarda nada: se cuentan los registros de
`asistencia` del 2027-01-05 despues del pedido. El `loc` de cada error se
compara con su final (`asistencias`, indice entero y campo), como lo arma la
validacion de FastAPI.
"""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    contar_asistencias,
    crear_alumno,
    crear_familia,
    crear_usuario,
    crear_vigente,
    cuerpo_guardado,
    errores_con_loc_terminado_en,
    ingresar,
    inscribir,
    insertar_grupo,
    url_asistencia,
)

DIA = date(2027, 1, 5)

# --- fixtures --------------------------------------------------------------


@pytest.fixture
def vigente(sesion: Session) -> int:
    return crear_vigente(sesion)


@pytest.fixture
def coordinador_id(sesion: Session) -> int:
    return crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)


@pytest.fixture
def coordinador(cliente: TestClient, coordinador_id: int) -> dict[str, str]:
    return ingresar(cliente, "coordi")


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    return insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def juan_en_delfines(
    sesion: Session, vigente: int, delfines_manana: int, coordinador_id: int
) -> int:
    juan = crear_alumno(sesion, "Juan", "Pérez")
    return inscribir(sesion, juan, delfines_manana, vigente, "manana", coordinador_id)


def _msgs(errores: list[dict[str, Any]]) -> list[str]:
    return [e["msg"] for e in errores]


# --- Requirement: El cuerpo del guardado -----------------------------------


class TestElCuerpoDelGuardado:
    def test_una_lista_vacia_responde_422_en_asistencias(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        juan_en_delfines: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Lista vacía
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json={"asistencias": []},
            headers=coordinador,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias")
        assert _msgs(errores) == ["Tiene que haber al menos un alumno."], respuesta.text
        assert contar_asistencias(sesion, DIA) == 0

    def test_un_elemento_sin_presente_responde_422_en_asistencias_0_presente(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        juan_en_delfines: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Falta presente
        # La inscripcion es valida y del grupo: lo unico que falla es `presente`.
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json={"asistencias": [{"inscripcion_id": juan_en_delfines}]},
            headers=coordinador,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias", 0, "presente")
        assert _msgs(errores) == ["Este dato es obligatorio."], respuesta.text
        assert contar_asistencias(sesion, DIA) == 0

    def test_una_inscripcion_de_otro_grupo_responde_422_y_no_guarda_ni_la_de_juan(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Inscripción de otro grupo
        tiburones = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        familia = crear_familia(sesion)
        juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia)
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=familia, nacimiento=date(2018, 7, 5))
        juan_en_delfines = inscribir(
            sesion, juan, delfines_manana, vigente, "manana", coordinador_id
        )
        ana_en_tiburones = inscribir(sesion, ana, tiburones, vigente, "manana", coordinador_id)

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan_en_delfines, True), (ana_en_tiburones, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias", 1, "inscripcion_id")
        assert _msgs(errores) == ["Esa inscripción no es de este grupo."], respuesta.text
        # El elemento 0 es valido: no tiene error propio.
        assert not errores_con_loc_terminado_en(respuesta, "asistencias", 0, "inscripcion_id")
        assert contar_asistencias(sesion, DIA) == 0

    def test_una_inscripcion_que_no_existe_responde_422_en_asistencias_0(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        juan_en_delfines: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Inscripción que no existe
        assert juan_en_delfines != 999999

        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((999999, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias", 0, "inscripcion_id")
        assert _msgs(errores) == ["Esa inscripción no es de este grupo."], respuesta.text
        assert contar_asistencias(sesion, DIA) == 0

    def test_una_inscripcion_repetida_responde_422_en_la_segunda_y_no_guarda_nada(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        juan_en_delfines: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Inscripción repetida
        respuesta = cliente.put(
            url_asistencia(delfines_manana, "2027-01-05"),
            json=cuerpo_guardado((juan_en_delfines, True), (juan_en_delfines, False)),
            headers=coordinador,
        )

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "asistencias", 1, "inscripcion_id")
        assert _msgs(errores) == ["Esa inscripción ya está en la lista."], respuesta.text
        assert not errores_con_loc_terminado_en(respuesta, "asistencias", 0, "inscripcion_id")
        assert contar_asistencias(sesion, DIA) == 0
