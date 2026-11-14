"""Capability `asistencia`: abrir la asistencia de un grupo en una fecha.

Un test por Scenario de `openspec/changes/asistencia/specs/asistencia/spec.md`,
Requirement «Abrir la asistencia de un grupo en una fecha»
(`GET /api/v1/grupos/{grupo_id}/asistencias/{fecha}`).

Los Scenarios del `PUT` (Requirement «Guardar la asistencia de un grupo en
una fecha») van en este mismo archivo, en su propia clase, en la tarea
siguiente.

Los alumnos se insertan en un orden distinto del esperado en la respuesta,
para que el orden por apellido y nombre no salga gratis del orden de
insercion.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    CAMPOS_DEL_ALUMNO,
    crear_alumno,
    crear_cerrada,
    crear_familia,
    crear_usuario,
    crear_vigente,
    ingresar,
    inscribir,
    insertar_grupo,
    nombres_y_presente,
    registrar_asistencia,
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
def delfines_manana(sesion: Session, vigente: int) -> int:
    return insertar_grupo(sesion, vigente, "Delfines", "manana")


@pytest.fixture
def tres_en_delfines(
    sesion: Session, vigente: int, delfines_manana: int, coordinador_id: int
) -> dict[str, int]:
    """Juan Perez, Sofia Ruiz y Martin Gomez inscriptos en «Delfines» manana.

    Se insertan Ruiz, Perez, Gomez: al reves del orden esperado.
    Devuelve la inscripcion de cada uno, por apellido.
    """
    inscripciones: dict[str, int] = {}
    for nombre, apellido in (("Sofía", "Ruiz"), ("Juan", "Pérez"), ("Martín", "Gómez")):
        alumno = crear_alumno(sesion, nombre, apellido)
        inscripciones[apellido] = inscribir(
            sesion, alumno, delfines_manana, vigente, "manana", coordinador_id
        )
    return inscripciones


# --- Requirement: Abrir la asistencia de un grupo en una fecha -------------


class TestAbrirLaAsistencia:
    def test_sin_asistencia_tomada_trae_a_los_tres_por_apellido_con_presente_null(
        self,
        cliente: TestClient,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Asistencia todavía no tomada
        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == delfines_manana
        assert cuerpo["grupo"] == "Delfines"
        assert cuerpo["turno"] == "manana"
        assert cuerpo["fecha"] == "2027-01-05"
        assert nombres_y_presente(cuerpo) == [
            ("Martín", "Gómez", None),
            ("Juan", "Pérez", None),
            ("Sofía", "Ruiz", None),
        ]
        assert [a["inscripcion_id"] for a in cuerpo["alumnos"]] == [
            tres_en_delfines["Gómez"],
            tres_en_delfines["Pérez"],
            tres_en_delfines["Ruiz"],
        ]

    def test_con_asistencia_tomada_trae_presentes_y_ausente_de_esa_fecha(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Asistencia ya tomada
        dia = date(2027, 1, 5)
        registrar_asistencia(sesion, tres_en_delfines["Pérez"], dia, True, coordinador_id)
        registrar_asistencia(sesion, tres_en_delfines["Ruiz"], dia, True, coordinador_id)
        registrar_asistencia(sesion, tres_en_delfines["Gómez"], dia, False, coordinador_id)
        # Ruido: el dia anterior, lo contrario. Si la consulta no filtrara
        # por fecha, saldrian estos valores o filas duplicadas.
        otro_dia = date(2027, 1, 4)
        registrar_asistencia(sesion, tres_en_delfines["Pérez"], otro_dia, False, coordinador_id)
        registrar_asistencia(sesion, tres_en_delfines["Ruiz"], otro_dia, False, coordinador_id)
        registrar_asistencia(sesion, tres_en_delfines["Gómez"], otro_dia, True, coordinador_id)

        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        assert nombres_y_presente(respuesta.json()) == [
            ("Martín", "Gómez", False),
            ("Juan", "Pérez", True),
            ("Sofía", "Ruiz", True),
        ]

    def test_lo_registrado_otro_dia_no_aparece_y_martin_trae_presente_null(
        self,
        cliente: TestClient,
        sesion: Session,
        delfines_manana: int,
        tres_en_delfines: dict[str, int],
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Lo registrado otro día no aparece
        registrar_asistencia(
            sesion, tres_en_delfines["Gómez"], date(2027, 1, 5), False, coordinador_id
        )

        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-01-06"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["fecha"] == "2027-01-06"
        martin = [a for a in cuerpo["alumnos"] if a["apellido"] == "Gómez"]
        assert len(martin) == 1, cuerpo
        assert martin[0]["presente"] is None

        # Contraste: en el 2027-01-05 el registro si se ve, asi que el null
        # de arriba se debe a la fecha y no a que nunca se lea la tabla.
        del_dia = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=coordinador)
        assert del_dia.status_code == 200, del_dia.text
        martin_del_dia = [a for a in del_dia.json()["alumnos"] if a["apellido"] == "Gómez"]
        assert [a["presente"] for a in martin_del_dia] == [False]

    def test_trae_solo_a_juan_con_la_inscripcion_de_pulpos_tarde(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Solo los inscriptos en ese grupo
        pulpos_tarde = insertar_grupo(sesion, vigente, "Pulpos", "tarde")
        tiburones_manana = insertar_grupo(sesion, vigente, "Tiburones", "manana")
        familia = crear_familia(sesion)
        juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia)
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=familia, nacimiento=date(2018, 7, 5))
        # La de la manana se crea primero: si la respuesta tomara la primera
        # inscripcion del alumno, saldria esta.
        juan_manana = inscribir(sesion, juan, delfines_manana, vigente, "manana", coordinador_id)
        juan_tarde = inscribir(sesion, juan, pulpos_tarde, vigente, "tarde", coordinador_id)
        inscribir(sesion, ana, tiburones_manana, vigente, "manana", coordinador_id)
        # Juan presente a la manana del mismo dia: en «Pulpos» tarde no se
        # tomo, asi que tiene que venir null y no true.
        registrar_asistencia(sesion, juan_manana, date(2027, 1, 5), True, coordinador_id)

        respuesta = cliente.get(url_asistencia(pulpos_tarde, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == pulpos_tarde
        assert cuerpo["grupo"] == "Pulpos"
        assert cuerpo["turno"] == "tarde"
        assert nombres_y_presente(cuerpo) == [("Juan", "Pérez", None)]
        assert cuerpo["alumnos"][0]["inscripcion_id"] == juan_tarde
        assert cuerpo["alumnos"][0]["inscripcion_id"] != juan_manana

    def test_un_grupo_sin_inscriptos_responde_200_con_alumnos_vacia(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        tres_en_delfines: dict[str, int],
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo sin alumnos inscriptos
        # «Delfines» manana tiene tres inscriptos en la misma temporada: si
        # la consulta no filtrara por grupo, aparecerian aca.
        caballitos_tarde = insertar_grupo(sesion, vigente, "Caballitos", "tarde")

        respuesta = cliente.get(url_asistencia(caballitos_tarde, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == caballitos_tarde
        assert cuerpo["grupo"] == "Caballitos"
        assert cuerpo["turno"] == "tarde"
        assert cuerpo["alumnos"] == []

    def test_cada_alumno_trae_exactamente_inscripcion_nombre_apellido_y_presente(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Sin datos médicos ni de familia
        familia = crear_familia(sesion, "socio")
        juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia)
        inscribir(sesion, juan, delfines_manana, vigente, "manana", coordinador_id)

        respuesta = cliente.get(url_asistencia(delfines_manana, "2027-01-05"), headers=coordinador)

        assert respuesta.status_code == 200, respuesta.text
        alumnos = respuesta.json()["alumnos"]
        assert len(alumnos) == 1, alumnos
        for alumno in alumnos:
            assert set(alumno) == CAMPOS_DEL_ALUMNO

    def test_un_grupo_de_la_temporada_cerrada_se_consulta_con_juan_presente(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        delfines_manana: int,
        coordinador_id: int,
    ) -> None:
        # Scenario: Grupo de una temporada cerrada se puede consultar
        # «Delfines» manana existe en las dos temporadas: tiene que salir el
        # de la cerrada, el del path.
        cerrada = crear_cerrada(sesion)
        delfines_viejo = insertar_grupo(sesion, cerrada, "Delfines", "manana")
        juan = crear_alumno(sesion, "Juan", "Pérez")
        juan_viejo = inscribir(sesion, juan, delfines_viejo, cerrada, "manana", coordinador_id)
        registrar_asistencia(sesion, juan_viejo, date(2026, 1, 6), True, coordinador_id)
        crear_usuario(sesion, "admin1", RolUsuario.ADMIN)

        respuesta = cliente.get(
            url_asistencia(delfines_viejo, "2026-01-06"), headers=ingresar(cliente, "admin1")
        )

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["grupo_id"] == delfines_viejo
        assert cuerpo["fecha"] == "2026-01-06"
        assert nombres_y_presente(cuerpo) == [("Juan", "Pérez", True)]
        assert cuerpo["alumnos"][0]["inscripcion_id"] == juan_viejo
