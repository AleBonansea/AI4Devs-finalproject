"""Capability `asistencia`: grupos donde no se guarda asistencia.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «Grupos donde no se guarda asistencia».

En esta tarea van solo los Scenarios del `GET`: «Abrir un grupo que no
existe», «Id de grupo más grande que el máximo» y «Abrir un grupo inactivo»
(el inactivo es [SUPUESTO], pregunta abierta en `aclaraciones-cliente.md`).
Los del `PUT` (grupo que no existe, temporada cerrada, inactivo) se suman a
la misma clase en la tarea siguiente.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    MENSAJE_GRUPO_INEXISTENTE,
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
def coordinador_id(sesion: Session) -> int:
    return crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)


@pytest.fixture
def coordinador(cliente: TestClient, coordinador_id: int) -> dict[str, str]:
    return ingresar(cliente, "coordi")


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int, coordinador_id: int) -> int:
    """«Delfines» manana de la vigente, con Juan Perez inscripto: un grupo que
    si existe, para que haya algo que no se confunda con el 999999."""
    grupo = insertar_grupo(sesion, vigente, "Delfines", "manana")
    juan = crear_alumno(sesion, "Juan", "Pérez")
    inscribir(sesion, juan, grupo, vigente, "manana", coordinador_id)
    return grupo


# --- Requirement: Grupos donde no se guarda asistencia ---------------------


class TestGruposDondeNoSeGuardaAsistencia:
    def test_abrir_un_grupo_que_no_existe_responde_404(
        self,
        cliente: TestClient,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Abrir un grupo que no existe
        assert delfines_manana != 999999

        respuesta = cliente.get(url_asistencia(999999, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_INEXISTENTE

    def test_un_id_de_grupo_mas_grande_que_el_maximo_responde_404(
        self,
        cliente: TestClient,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Id de grupo más grande que el máximo
        # 9223372036854775808 es el maximo de bigint mas uno.
        respuesta = cliente.get(
            url_asistencia("9223372036854775808", "2027-01-05"), headers=coordinador
        )

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_INEXISTENTE

    def test_abrir_un_grupo_inactivo_responde_200_con_juan(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Abrir un grupo inactivo
        pulpos_manana = insertar_grupo(sesion, vigente, "Pulpos", "manana", activo=False)
        juan = crear_alumno(sesion, "Juan", "Pérez")
        inscripcion = inscribir(sesion, juan, pulpos_manana, vigente, "manana", coordinador_id)

        respuesta = cliente.get(url_asistencia(pulpos_manana, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == pulpos_manana
        assert cuerpo["grupo"] == "Pulpos"
        assert nombres_y_presente(cuerpo) == [("Juan", "Pérez", None)]
        assert cuerpo["alumnos"][0]["inscripcion_id"] == inscripcion


# --- Requirement: Grupos donde no se guarda asistencia (PUT) ---------------
# Tarea 2.2. Clase aparte e imports aca abajo para no tocar lo que ya estaba.
# Cada pedido lleva un cuerpo valido para el grupo del path, asi el unico
# motivo de rechazo posible es el grupo.

from datetime import date  # noqa: E402

from tests.functional.asistencia.preparacion import (  # noqa: E402
    contar_asistencias,
    crear_cerrada,
    cuerpo_guardado,
    inscripciones_del_grupo,
)


class TestGruposDondeNoSeGuardaAsistenciaAlGuardar:
    def test_guardar_en_un_grupo_que_no_existe_responde_404(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Guardar en un grupo que no existe
        assert delfines_manana != 999999
        [juan] = inscripciones_del_grupo(sesion, delfines_manana)

        respuesta = cliente.put(
            url_asistencia(999999, "2027-01-05"),
            json=cuerpo_guardado((juan, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_GRUPO_INEXISTENTE
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0

    def test_guardar_en_un_grupo_de_la_temporada_cerrada_responde_409_y_no_guarda(
        self,
        cliente: TestClient,
        sesion: Session,
        coordinador_id: int,
    ) -> None:
        # Scenario: Guardar en un grupo de una temporada cerrada
        cerrada = crear_cerrada(sesion)
        delfines_viejo = insertar_grupo(sesion, cerrada, "Delfines", "manana")
        juan = crear_alumno(sesion, "Juan", "Pérez")
        inscripcion = inscribir(sesion, juan, delfines_viejo, cerrada, "manana", coordinador_id)
        crear_usuario(sesion, "admin1", RolUsuario.ADMIN)

        respuesta = cliente.put(
            url_asistencia(delfines_viejo, "2026-01-06"),
            json=cuerpo_guardado((inscripcion, True)),
            headers=ingresar(cliente, "admin1"),
        )

        assert respuesta.status_code == 409, respuesta.text
        assert (
            respuesta.json()["detail"]
            == "El grupo es de una temporada cerrada, que queda solo para consulta."
        )
        assert contar_asistencias(sesion, date(2026, 1, 6)) == 0

    def test_guardar_en_un_grupo_inactivo_responde_409_y_no_guarda(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Guardar en un grupo inactivo ([SUPUESTO], pregunta abierta
        # en `aclaraciones-cliente.md`)
        pulpos_manana = insertar_grupo(sesion, vigente, "Pulpos", "manana", activo=False)
        juan = crear_alumno(sesion, "Juan", "Pérez")
        inscripcion = inscribir(sesion, juan, pulpos_manana, vigente, "manana", coordinador_id)

        respuesta = cliente.put(
            url_asistencia(pulpos_manana, "2027-01-05"),
            json=cuerpo_guardado((inscripcion, True)),
            headers=coordinador,
        )

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == "El grupo no está activo."
        assert contar_asistencias(sesion, date(2027, 1, 5)) == 0
