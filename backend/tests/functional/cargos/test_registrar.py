"""Capability `cargos`: registrar un cargo por la API.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirements «Registrar un cargo», «Un cargo registrado no se recalcula» y
«Saldo pendiente al registrar».

Montos y porcentajes viajan como texto con dos decimales: se comparan como
texto exacto ("85000.00"), sin tolerancia. Lo leido de la base se compara
como `Decimal` exacto.
"""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_alumno, crear_familia, inscribir
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    cargo_de,
    cargo_en_la_base,
    contar_cargos,
    descuento_modalidad,
    descuentos_mes,
    errores_con_loc_terminado_en,
    familia_con_hijos,
    hijo_inscripto,
    insertar_cargo_monto_fijo,
    preinscripcion,
    preparar_cerrada,
    preparar_vigente,
    registrar,
    tarifa,
    tipo_cargo,
    todos_los_descuentos,
)

# --- Requirement: Registrar un cargo -----------------------------------------


class TestRegistrarUnCargo:
    def test_el_abono_del_mes_se_registra_con_el_descuento_del_tramo_de_dos_hijos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Abono del Mes con descuento por cantidad de hijos
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00", 3: "20.00"})
        familia, (ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["categoria_aplicada"] == "empleado"
        assert cuerpo["cantidad_hijos_aplicada"] == 2
        assert cuerpo["monto_base"] == "100000.00"
        assert cuerpo["porcentaje_aplicado"] == "15.00"
        assert cuerpo["monto_total"] == "85000.00"
        assert cuerpo["familia_id"] == familia
        assert cuerpo["modalidad"] == "mes"
        assert cuerpo["periodo_cobro_id"] == v.mes_1
        assert cuerpo["saldo_pendiente"] == "85000.00"

        fila = cargo_en_la_base(sesion, cuerpo["id"])
        assert fila.creado_por == v.admin
        assert fila.temporada_id == v.temporada
        assert fila.familia_id == familia
        assert fila.alumno_id == juan.alumno
        assert fila.tipo_cargo_id == v.abono
        assert fila.inscripcion_id == juan.inscripcion
        assert fila.modalidad == "mes"
        assert fila.periodo_cobro_id == v.mes_1
        assert fila.categoria_aplicada == "empleado"
        assert fila.cantidad_hijos_aplicada == 2
        assert fila.monto_base == Decimal("100000.00")
        assert fila.porcentaje_aplicado == Decimal("15.00")
        assert fila.monto_total == Decimal("85000.00")

    def test_la_preinscripcion_se_registra_por_su_monto_fijo_sin_descuento_ni_datos_del_abono(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Preinscripción con monto fijo y sin descuento
        v = preparar_vigente(sesion)
        _, (juan,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=preinscripcion(v, juan.alumno)
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["categoria_aplicada"] == "socio"
        assert cuerpo["monto_base"] == "20000.00"
        assert cuerpo["porcentaje_aplicado"] == "0.00"
        assert cuerpo["monto_total"] == "20000.00"
        for campo in (
            "inscripcion_id",
            "modalidad",
            "periodo_cobro_id",
            "fecha_dia",
            "cantidad_hijos_aplicada",
        ):
            assert campo in cuerpo, f"Falta {campo} en la respuesta"
            assert cuerpo[campo] is None, f"{campo} = {cuerpo[campo]!r}, se esperaba null"

    def test_la_preinscripcion_vale_lo_mismo_para_una_familia_no_socio_y_una_socio(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: La Preinscripción no depende de la categoría
        v = preparar_vigente(sesion)
        todos_los_descuentos(sesion, v.temporada, "no_socio", "0.00")
        todos_los_descuentos(sesion, v.temporada, "socio", "50.00")
        _, (lucia,) = familia_con_hijos(sesion, v, "no_socio", ["Lucía"])
        _, (juan,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)

        de_no_socio = registrar(cliente, encabezados, preinscripcion(v, lucia.alumno))
        de_socio = registrar(cliente, encabezados, preinscripcion(v, juan.alumno))

        assert de_no_socio["monto_total"] == "20000.00"
        assert de_socio["monto_total"] == "20000.00"

    def test_el_abono_del_dia_se_registra_con_su_fecha_sin_periodo_ni_cantidad_de_hijos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Abono del Día
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "dia", "8000.00")
        descuento_modalidad(sesion, v.temporada, "empleado", "dia", "10.00")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, juan, "dia", fecha_dia="2027-01-05")
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["fecha_dia"] == "2027-01-05"
        assert cuerpo["periodo_cobro_id"] is None
        assert cuerpo["cantidad_hijos_aplicada"] is None
        assert cuerpo["monto_total"] == "7200.00"

    def test_un_alumno_sin_ningun_documento_recibe_el_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: La ficha incompleta no impide el cargo
        # Todavia no existe la documentacion: Juan no tiene ningun documento.
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text

    def test_un_importe_en_el_cuerpo_se_rechaza_con_422_y_no_se_guarda_ningun_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El importe no viene del cliente
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        antes = contar_cargos(sesion)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json={**abono_mes(v, juan), "monto_total": "1.00"},
        )

        assert respuesta.status_code == 422, respuesta.text
        assert errores_con_loc_terminado_en(respuesta, "monto_total"), respuesta.text
        assert contar_cargos(sesion) == antes


# --- Requirement: Un cargo registrado no se recalcula --------------------------


class TestUnCargoRegistradoNoSeRecalcula:
    def test_el_cargo_nuevo_usa_el_tramo_de_tres_y_el_del_mes_1_conserva_el_de_dos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Hijo que se suma a mitad de temporada
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00", 3: "20.00"})
        familia, (_ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
        encabezados = admin(cliente)
        mes_1 = registrar(cliente, encabezados, abono_mes(v, juan, v.mes_1))
        assert mes_1["cantidad_hijos_aplicada"] == 2
        assert mes_1["monto_total"] == "85000.00"

        # Despues se inscribe a Tomas en el turno manana.
        hijo_inscripto(sesion, v, familia, "Tomás", nacimiento=date(2021, 6, 1))

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan, v.mes_2))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["cantidad_hijos_aplicada"] == 3
        assert cuerpo["monto_total"] == "80000.00"

        anterior = cargo_de(sesion, juan.inscripcion, v.mes_1)
        assert anterior.cantidad_hijos_aplicada == 2
        assert anterior.monto_total == Decimal("85000.00")

    def test_el_cargo_nuevo_usa_la_tarifa_nueva_y_el_del_mes_1_conserva_la_anterior(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Cambia el tarifario después del cargo
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        mes_1 = registrar(cliente, encabezados, abono_mes(v, juan, v.mes_1))
        assert mes_1["monto_base"] == "100000.00"

        sesion.execute(
            text(
                "UPDATE tarifa_base SET monto = :m "
                "WHERE temporada_id = :t AND turno = 'manana' AND modalidad = 'mes'"
            ),
            {"m": Decimal("120000.00"), "t": v.temporada},
        )

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan, v.mes_2))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["monto_base"] == "120000.00"

        anterior = cargo_de(sesion, juan.inscripcion, v.mes_1)
        assert anterior.monto_base == Decimal("100000.00")
        assert anterior.monto_total == Decimal("90000.00")


# --- Requirement: Saldo pendiente al registrar ------------------------------------


class TestSaldoPendienteAlRegistrar:
    def test_el_saldo_suma_la_preinscripcion_de_ana_y_el_abono_nuevo_de_juan(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Segundo cargo de la familia
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        familia, (ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])
        insertar_cargo_monto_fijo(
            sesion,
            temporada_id=v.temporada,
            familia_id=familia,
            alumno_id=ana.alumno,
            tipo_cargo_id=v.preinscripcion,
            categoria="empleado",
            monto="20000.00",
            creado_por=v.admin,
        )
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["monto_total"] == "85000.00"
        assert cuerpo["saldo_pendiente"] == "105000.00"

    def test_el_saldo_no_suma_cargos_de_otra_temporada_ni_de_otra_familia(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Solo la familia y la temporada del cargo
        v = preparar_vigente(sesion)
        cerrada = preparar_cerrada(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        familia, (ana, juan) = familia_con_hijos(sesion, v, "empleado", ["Ana", "Juan"])

        # Cargo de 30000.00 de la familia Perez en la temporada cerrada.
        inscribir(sesion, ana.alumno, cerrada.delfines, cerrada.temporada, "manana", v.admin)
        preinscripcion_cerrada = tipo_cargo(
            sesion, cerrada.temporada, "Preinscripción", "monto_fijo", "30000.00"
        )
        insertar_cargo_monto_fijo(
            sesion,
            temporada_id=cerrada.temporada,
            familia_id=familia,
            alumno_id=ana.alumno,
            tipo_cargo_id=preinscripcion_cerrada,
            categoria="empleado",
            monto="30000.00",
            creado_por=v.admin,
        )

        # Cargo de 50000.00 de otra familia en 2026-27.
        otra_familia = crear_familia(sesion, "socio")
        sofia = crear_alumno(sesion, "Sofía", "Gómez", familia_id=otra_familia)
        inscribir(sesion, sofia, v.delfines, v.temporada, "manana", v.admin)
        equipo = tipo_cargo(sesion, v.temporada, "Equipo", "monto_fijo", "50000.00")
        insertar_cargo_monto_fijo(
            sesion,
            temporada_id=v.temporada,
            familia_id=otra_familia,
            alumno_id=sofia,
            tipo_cargo_id=equipo,
            categoria="socio",
            monto="50000.00",
            creado_por=v.admin,
        )
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["monto_total"] == "85000.00"
        assert cuerpo["saldo_pendiente"] == "85000.00"
