"""Capability `cargos`: falta configuración del tarifario.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirement «Falta configuración del tarifario».

Cada test carga el tarifario completo salvo justo la celda del Scenario, y
deja cargadas las vecinas (la misma modalidad en el otro turno, los otros
tramos, las otras modalidades): asi el 409 sale de la celda que falta y no
de un tarifario vacio.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_familia
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    contar_cargos,
    descuento_modalidad,
    descuentos_mes,
    familia_con_hijos,
    hijo_inscripto,
    preparar_vigente,
    tarifa,
    todos_los_descuentos,
)


class TestFaltaConfiguracionDelTarifario:
    def test_sin_tarifa_base_del_turno_y_la_modalidad_responde_409_y_no_guarda(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Falta la tarifa base
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "quincena", "45000.00")
        for modalidad in ("mes", "semana", "dia"):
            tarifa(sesion, v.temporada, "tarde", modalidad, "45000.00")
        todos_los_descuentos(sesion, v.temporada, "socio", "10.00")
        familia = crear_familia(sesion, "socio")
        lucia = hijo_inscripto(sesion, v, familia, "Lucía", "Martínez", turno="tarde")
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json=abono(v, lucia, "quincena", periodo_id=v.quincena_1),
        )

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == (
            "Falta la tarifa base del turno tarde para la modalidad Quincena."
        )
        assert contar_cargos(sesion) == 0

    def test_sin_porcentaje_del_tramo_responde_409_y_no_guarda(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Falta el porcentaje del tramo
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00", 4: "25.00"})
        for modalidad in ("dia", "semana", "quincena"):
            descuento_modalidad(sesion, v.temporada, "empleado", modalidad, "10.00")
        _, (_, juan, _) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan", "Tomás"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == (
            "Falta el descuento de la categoría empleado para el Mes con 3 hijos."
        )
        assert contar_cargos(sesion) == 0

    def test_sin_porcentaje_de_la_modalidad_responde_409_y_no_guarda(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Falta el porcentaje de la modalidad
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "semana", "30000.00")
        for modalidad in ("dia", "quincena"):
            descuento_modalidad(sesion, v.temporada, "socio", modalidad, "50.00")
        descuentos_mes(sesion, v.temporada, "socio", {t: "50.00" for t in (1, 2, 3, 4)})
        _, (hijo,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, hijo, "semana", periodo_id=v.semana_1)
        )

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == (
            "Falta el descuento de la categoría socio para la modalidad Semana."
        )
        assert contar_cargos(sesion) == 0
