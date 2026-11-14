"""Capability `cargos`: simular un cargo.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirement «Simular un cargo».
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    URL_SIMULACION,
    abono_mes,
    admin,
    contar_cargos,
    descuentos_mes,
    familia_con_hijos,
    preparar_vigente,
    registrar,
    tarifa,
)


class TestSimularUnCargo:
    def test_la_simulacion_devuelve_el_desglose_y_no_guarda_ningun_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Simular el Abono del Mes
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        familia, (_ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
        encabezados = admin(cliente)
        antes = contar_cargos(sesion)

        respuesta = cliente.post(URL_SIMULACION, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["familia_id"] == familia
        assert cuerpo["categoria_aplicada"] == "empleado"
        assert cuerpo["cantidad_hijos_aplicada"] == 2
        assert cuerpo["monto_base"] == "100000.00"
        assert cuerpo["porcentaje_aplicado"] == "15.00"
        assert cuerpo["monto_total"] == "85000.00"
        assert contar_cargos(sesion) == antes

    def test_simular_un_cargo_ya_registrado_responde_409_igual_que_registrarlo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Simular un cargo que ya existe
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        registrar(cliente, encabezados, abono_mes(v, juan))

        simulacion = cliente.post(URL_SIMULACION, headers=encabezados, json=abono_mes(v, juan))
        registro = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert simulacion.status_code == 409, simulacion.text
        assert registro.status_code == 409, registro.text
        assert simulacion.json()["detail"] == registro.json()["detail"]
        assert contar_cargos(sesion) == 1
