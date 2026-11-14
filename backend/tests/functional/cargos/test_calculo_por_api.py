"""Capability `cargos`: el calculo del Abono, comprobado por la API.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirements «Un único porcentaje sobre la tarifa base» y «El tramo de hijos
del Mes».

A diferencia de `test_calculo_cargo.py`, que prueba la funcion pura, aca
cuenta lo que el servicio pone alrededor: que lea la tarifa del turno de la
inscripcion, que cuente los hijos de la familia en ese turno y esa temporada,
y que el total pase el `CHECK` de la base (el medio centavo).

Cada test carga su propio tarifario con los valores de su Scenario.
"""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_alumno, crear_familia, inscribir
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    cargo_en_la_base,
    descuento_modalidad,
    descuentos_mes,
    familia_con_hijos,
    hijo_inscripto,
    preparar_cerrada,
    preparar_vigente,
    registrar,
    tarifa,
    todos_los_descuentos,
)

NO_SOCIO_MES = {1: "0.00", 2: "10.00", 3: "15.00", 4: "20.00"}


# --- Requirement: Un único porcentaje sobre la tarifa base --------------------------


class TestUnUnicoPorcentaje:
    def test_en_la_semana_se_aplica_el_porcentaje_de_la_modalidad_y_no_el_del_tramo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: En la Semana no cuentan los hijos
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "semana", "30000.00")
        descuento_modalidad(sesion, v.temporada, "empleado", "semana", "10.00")
        descuentos_mes(sesion, v.temporada, "empleado", {3: "20.00"})
        _, hijos = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan", "Tomás"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json=abono(v, hijos[1], "semana", periodo_id=v.semana_1),
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["porcentaje_aplicado"] == "10.00"
        assert cuerpo["cantidad_hijos_aplicada"] is None
        assert cuerpo["monto_total"] == "27000.00"

    def test_la_quincena_de_la_tarde_usa_la_tarifa_de_la_tarde(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Quincena de la tarde
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "tarde", "quincena", "45000.00")
        # La manana con otra tarifa: si el servicio leyera el turno
        # equivocado, el monto base lo delataria.
        tarifa(sesion, v.temporada, "manana", "quincena", "60000.00")
        descuento_modalidad(sesion, v.temporada, "socio", "quincena", "50.00")
        _, (hijo,) = familia_con_hijos(sesion, v, "socio", ["Juan"], turno="tarde")
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json=abono(v, hijo, "quincena", periodo_id=v.quincena_1),
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["monto_base"] == "45000.00"
        assert cuerpo["monto_total"] == "22500.00"

    def test_con_todo_al_50_se_aplica_un_solo_50_y_no_se_acumula(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un solo porcentaje, nunca acumulado
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        todos_los_descuentos(sesion, v.temporada, "socio", "50.00")
        _, hijos = familia_con_hijos(sesion, v, "socio", ["Ana", "Juan", "Tomás", "Sol"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, hijos[0]))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["porcentaje_aplicado"] == "50.00"
        assert cuerpo["monto_total"] == "50000.00"
        assert cuerpo["monto_total"] not in ("25000.00", "0.00")

    def test_un_porcentaje_con_decimales_se_aplica_exacto(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Porcentaje con decimales
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {3: "36.25"})
        _, hijos = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan", "Tomás"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, hijos[2]))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["porcentaje_aplicado"] == "36.25"
        assert cuerpo["monto_total"] == "63750.00"

    def test_medio_centavo_se_redondea_hacia_arriba_y_el_cargo_queda_en_la_base(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Medio centavo se redondea hacia arriba
        # 1000.05 * 0.5 = 500.025. Pasa por la base: el `CHECK` del total
        # exige 500.03, asi que un redondeo distinto daria error, no 201.
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "dia", "1000.05")
        descuento_modalidad(sesion, v.temporada, "socio", "dia", "50.00")
        _, (hijo,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, hijo, "dia", fecha_dia="2027-01-05")
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["monto_total"] == "500.03"
        assert cuerpo["monto_total"] != "500.02"
        fila = cargo_en_la_base(sesion, cuerpo["id"])
        assert fila.monto_base == Decimal("1000.05")
        assert fila.monto_total == Decimal("500.03")


# --- Requirement: El tramo de hijos del Mes --------------------------------------------


class TestElTramoDeHijosDelMes:
    def test_un_solo_hijo_toma_el_tramo_de_uno_y_no_el_de_dos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un solo hijo no toma el tramo de dos
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "no_socio", NO_SOCIO_MES)
        _, (hijo,) = familia_con_hijos(sesion, v, "no_socio", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, hijo))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["cantidad_hijos_aplicada"] == 1
        assert cuerpo["porcentaje_aplicado"] == "0.00"
        assert cuerpo["monto_total"] == "100000.00"
        assert cuerpo["monto_total"] != "90000.00"

    def test_tres_hijos_toman_el_tramo_de_tres(self, cliente: TestClient, sesion: Session) -> None:
        # Scenario: Tres hijos
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "no_socio", NO_SOCIO_MES)
        _, hijos = familia_con_hijos(sesion, v, "no_socio", ["Ana", "Juan", "Tomás"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, hijos[1]))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["cantidad_hijos_aplicada"] == 3
        assert cuerpo["monto_total"] == "85000.00"

    def test_el_porcentaje_del_tramo_alcanza_a_los_cuatro_hijos_incluido_el_primero(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El tramo alcanza a todos los hijos
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "no_socio", NO_SOCIO_MES)
        _, hijos = familia_con_hijos(sesion, v, "no_socio", ["Ana", "Juan", "Tomás", "Sol"])
        encabezados = admin(cliente)

        cargos = [registrar(cliente, encabezados, abono_mes(v, hijo, v.mes_1)) for hijo in hijos]

        for hijo, cargo in zip(hijos, cargos, strict=True):
            assert cargo["alumno_id"] == hijo.alumno
            assert cargo["porcentaje_aplicado"] == "20.00", cargo
            assert cargo["monto_total"] == "80000.00", cargo

    def test_cinco_hijos_usan_el_tramo_de_cuatro_o_mas(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cinco hijos usan el tramo de cuatro o más
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "no_socio", NO_SOCIO_MES)
        _, hijos = familia_con_hijos(sesion, v, "no_socio", ["Ana", "Juan", "Tomás", "Sol", "Leo"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, hijos[4]))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["cantidad_hijos_aplicada"] == 5
        assert cuerpo["porcentaje_aplicado"] == "20.00"
        assert cuerpo["monto_total"] == "80000.00"

    def test_los_hijos_se_cuentan_en_el_turno_de_la_inscripcion_del_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Los hijos se cuentan por turno
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        tarifa(sesion, v.temporada, "tarde", "mes", "80000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        familia, (_ana, juan_manana) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
        juan_tarde = inscribir(sesion, juan_manana.alumno, v.pulpos, v.temporada, "tarde", v.admin)
        encabezados = admin(cliente)

        manana = registrar(cliente, encabezados, abono_mes(v, juan_manana, v.mes_1))
        tarde = registrar(
            cliente,
            encabezados,
            {**abono_mes(v, juan_manana, v.mes_1), "inscripcion_id": juan_tarde},
        )

        assert manana["cantidad_hijos_aplicada"] == 2
        assert manana["monto_total"] == "85000.00"
        assert tarde["cantidad_hijos_aplicada"] == 1
        assert tarde["monto_total"] == "72000.00"

    def test_un_hermano_inscripto_solo_en_la_temporada_cerrada_no_cuenta(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un hermano de otra temporada no cuenta
        v = preparar_vigente(sesion)
        cerrada = preparar_cerrada(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        familia = crear_familia(sesion, "empleado")
        ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=familia, nacimiento=date(2017, 3, 10))
        inscribir(sesion, ana, cerrada.delfines, cerrada.temporada, "manana", v.admin)
        juan = hijo_inscripto(sesion, v, familia, "Juan", nacimiento=date(2019, 3, 10))
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["cantidad_hijos_aplicada"] == 1
