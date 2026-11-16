"""Capability `cargos`: el cargo y su temporada.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirements «El alumno está inscripto en la temporada», «La fecha del Día
está dentro de la temporada» y «La temporada cerrada queda para consulta».

La temporada vigente 2026-27 va del 2027-01-04 al 2027-02-26: el primer y
el ultimo dia son el caso de adentro, el anterior y el posterior el de
afuera.
"""

from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_alumno, crear_familia, inscribir
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    admin,
    contar_cargos,
    familia_con_hijos,
    hijo_inscripto,
    periodo,
    preinscripcion,
    preparar_cerrada,
    preparar_vigente,
    tipo_cargo,
)
from tests.functional.cargos.rechazos import exigir_rechazo, tarifario_completo

FUERA_DE_TEMPORADA = "La fecha está fuera de la temporada, del 04/01/2027 al 26/02/2027."


# --- Requirement: El alumno está inscripto en la temporada -------------------


class TestElAlumnoEstaInscriptoEnLaTemporada:
    def test_la_preinscripcion_de_un_alumno_inscripto_solo_en_la_temporada_anterior_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Preinscripción de un alumno inscripto solo en la temporada anterior
        v = preparar_vigente(sesion)
        c = preparar_cerrada(sesion)
        tarifario_completo(sesion, v.temporada, "socio")
        familia = crear_familia(sesion, "socio")
        sofia = crear_alumno(sesion, "Sofía", "Gómez", familia_id=familia)
        inscribir(sesion, sofia, c.delfines, c.temporada, "manana", v.admin)
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=preinscripcion(v, sofia))

        exigir_rechazo(respuesta, {"alumno_id": "El alumno no está inscripto en la temporada."})
        assert contar_cargos(sesion) == 0

    def test_la_preinscripcion_de_un_alumno_inscripto_solo_a_la_tarde_se_registra(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Preinscripción de un alumno inscripto solo a la tarde
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "socio")
        familia = crear_familia(sesion, "socio")
        lucia = hijo_inscripto(sesion, v, familia, "Lucía", "Martínez", turno="tarde")
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=preinscripcion(v, lucia.alumno)
        )

        assert respuesta.status_code == 201, respuesta.text
        assert contar_cargos(sesion) == 1


# --- Requirement: La fecha del Día está dentro de la temporada ---------------


class TestLaFechaDelDiaEstaDentroDeLaTemporada:
    def _pedir_dia(self, cliente: TestClient, sesion: Session, fecha: str) -> Any:
        """Un «Abono» del Dia de Juan con la fecha dada, con el resto valido."""
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        return cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, juan, "dia", fecha_dia=fecha)
        )

    def test_el_primer_dia_de_la_temporada_se_registra(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Primer día de la temporada
        respuesta = self._pedir_dia(cliente, sesion, "2027-01-04")

        assert respuesta.status_code == 201, respuesta.text
        assert contar_cargos(sesion) == 1

    def test_el_dia_anterior_al_inicio_se_rechaza_con_las_fechas_de_la_temporada(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Día anterior al inicio
        respuesta = self._pedir_dia(cliente, sesion, "2027-01-03")

        exigir_rechazo(respuesta, {"fecha_dia": FUERA_DE_TEMPORADA})
        assert contar_cargos(sesion) == 0

    def test_el_ultimo_dia_de_la_temporada_se_registra(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Último día de la temporada
        respuesta = self._pedir_dia(cliente, sesion, "2027-02-26")

        assert respuesta.status_code == 201, respuesta.text
        assert contar_cargos(sesion) == 1

    def test_el_dia_posterior_al_cierre_se_rechaza_con_el_mismo_mensaje(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Día posterior al cierre
        respuesta = self._pedir_dia(cliente, sesion, "2027-02-27")

        exigir_rechazo(respuesta, {"fecha_dia": FUERA_DE_TEMPORADA})
        assert contar_cargos(sesion) == 0


# --- Requirement: La temporada cerrada queda para consulta -------------------


class TestLaTemporadaCerradaQuedaParaConsulta:
    def test_un_cargo_con_el_tipo_de_la_temporada_cerrada_se_rechaza_y_no_guarda(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cargo en la temporada anterior
        # La cerrada tiene todo lo que el cargo necesitaria (tipo, periodo,
        # tarifario, Juan inscripto): el unico motivo de rechazo es que esta
        # cerrada.
        v = preparar_vigente(sesion)
        c = preparar_cerrada(sesion)
        abono_cerrada = tipo_cargo(sesion, c.temporada, "Abono", "tarifario", None)
        mes_1_cerrada = periodo(
            sesion, c.temporada, "mes", "Mes 1", date(2026, 1, 5), date(2026, 1, 30)
        )
        tarifario_completo(sesion, c.temporada, "empleado")
        familia = crear_familia(sesion, "empleado")
        juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia)
        inscripcion = inscribir(sesion, juan, c.delfines, c.temporada, "manana", v.admin)
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json={
                "alumno_id": juan,
                "tipo_cargo_id": abono_cerrada,
                "inscripcion_id": inscripcion,
                "modalidad": "mes",
                "periodo_cobro_id": mes_1_cerrada,
            },
        )

        exigir_rechazo(
            respuesta,
            {
                "tipo_cargo_id": (
                    "El tipo de cargo es de una temporada cerrada, que queda solo para consulta."
                )
            },
        )
        assert contar_cargos(sesion) == 0
