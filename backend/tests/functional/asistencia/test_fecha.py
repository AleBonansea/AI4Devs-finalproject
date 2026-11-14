"""Capability `asistencia`: la fecha esta dentro de la temporada del grupo.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «La fecha está dentro de la temporada del grupo».

En esta tarea van solo los Scenarios del `GET`: «Abrir una fecha fuera de la
temporada» y «Fecha mal escrita». Los del `PUT` (primer y ultimo dia, dia
anterior al inicio y posterior al cierre) se suman a la misma clase en la
tarea siguiente.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    MENSAJE_FUERA_DE_TEMPORADA_VIGENTE,
    crear_alumno,
    crear_usuario,
    crear_vigente,
    errores_con_loc_terminado_en,
    ingresar,
    inscribir,
    insertar_grupo,
    url_asistencia,
)

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
def delfines_manana(sesion: Session, vigente: int, coordinador_id: int) -> int:
    """«Delfines» manana de la vigente, con Juan Perez inscripto."""
    grupo = insertar_grupo(sesion, vigente, "Delfines", "manana")
    juan = crear_alumno(sesion, "Juan", "Pérez")
    inscribir(sesion, juan, grupo, vigente, "manana", coordinador_id)
    return grupo


# --- Requirement: La fecha está dentro de la temporada del grupo -----------


class TestLaFechaEstaDentroDeLaTemporada:
    def test_abrir_una_fecha_fuera_de_la_temporada_responde_422_con_el_rango(
        self,
        cliente: TestClient,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Abrir una fecha fuera de la temporada
        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-03-01"), headers=coordinador)

        assert respuesta.status_code == 422, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FUERA_DE_TEMPORADA_VIGENTE
        assert "Juan" not in respuesta.text

        # Los bordes, segun el Requirement (los dos extremos incluidos): el
        # dia siguiente al cierre y el anterior al inicio quedan afuera; el
        # ultimo y el primero, adentro.
        for fuera in ("2027-02-27", "2027-01-03"):
            r = cliente.get(url_asistencia(delfines_manana, fuera), headers=coordinador)
            assert r.status_code == 422, (fuera, r.text)
            assert r.json()["detail"] == MENSAJE_FUERA_DE_TEMPORADA_VIGENTE
        for dentro in ("2027-02-26", "2027-01-04"):
            r = cliente.get(url_asistencia(delfines_manana, dentro), headers=coordinador)
            assert r.status_code == 200, (dentro, r.text)
            assert r.json()["fecha"] == dentro

    def test_una_fecha_mal_escrita_responde_422_en_fecha(
        self,
        cliente: TestClient,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Fecha mal escrita
        respuesta = cliente.get(url_asistencia(delfines_manana, "05-01-2027"), headers=coordinador)

        assert respuesta.status_code == 422, respuesta.text
        errores = errores_con_loc_terminado_en(respuesta, "fecha")
        assert errores, f"no hay error en fecha: {respuesta.text}"
        assert [e["msg"] for e in errores] == ["La fecha no es válida."], respuesta.text


# --- Requirement: La fecha está dentro de la temporada del grupo (PUT) -----
# Tarea 2.2. Clase aparte e imports aca abajo para no tocar lo que ya estaba.

from datetime import date  # noqa: E402

from httpx import Response  # noqa: E402

from tests.functional.asistencia.preparacion import (  # noqa: E402
    contar_asistencias,
    cuerpo_guardado,
    inscripciones_del_grupo,
    nombres_y_presente,
)


def _guardar_juan(
    cliente: TestClient, sesion: Session, grupo: int, fecha: str, headers: dict[str, str]
) -> Response:
    """PUT con Juan Perez, el unico inscripto del grupo, `presente` true."""
    [juan] = inscripciones_del_grupo(sesion, grupo)
    return cliente.put(
        url_asistencia(grupo, fecha), json=cuerpo_guardado((juan, True)), headers=headers
    )


class TestLaFechaEstaDentroDeLaTemporadaAlGuardar:
    def test_guardar_el_primer_dia_de_la_temporada_responde_200(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Primer día de la temporada
        respuesta = _guardar_juan(cliente, sesion, delfines_manana, "2027-01-04", coordinador)

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["fecha"] == "2027-01-04"
        assert nombres_y_presente(respuesta.json()) == [("Juan", "Pérez", True)]
        assert contar_asistencias(sesion, date(2027, 1, 4)) == 1

    def test_guardar_el_dia_anterior_al_inicio_responde_422_y_no_guarda(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Día anterior al inicio
        respuesta = _guardar_juan(cliente, sesion, delfines_manana, "2027-01-03", coordinador)

        assert respuesta.status_code == 422, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FUERA_DE_TEMPORADA_VIGENTE
        assert contar_asistencias(sesion, date(2027, 1, 3)) == 0

    def test_guardar_el_ultimo_dia_de_la_temporada_responde_200(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Último día de la temporada
        respuesta = _guardar_juan(cliente, sesion, delfines_manana, "2027-02-26", coordinador)

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["fecha"] == "2027-02-26"
        assert nombres_y_presente(respuesta.json()) == [("Juan", "Pérez", True)]
        assert contar_asistencias(sesion, date(2027, 2, 26)) == 1

    def test_guardar_el_dia_posterior_al_cierre_responde_422(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Día posterior al cierre
        respuesta = _guardar_juan(cliente, sesion, delfines_manana, "2027-02-27", coordinador)

        assert respuesta.status_code == 422, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FUERA_DE_TEMPORADA_VIGENTE
        assert contar_asistencias(sesion, date(2027, 2, 27)) == 0
