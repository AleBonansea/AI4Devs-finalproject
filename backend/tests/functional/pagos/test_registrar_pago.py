"""Capability `pagos`: registrar un pago (change cuenta-corriente, tarea 2.1).

Un test por Scenario de `openspec/changes/cuenta-corriente/specs/pagos/spec.md`,
Requirement «Registrar un pago», salvo «El saldo del cargo coincide con la
cuenta corriente», que necesita el `GET` de la cuenta corriente (tarea 3.1).

Endpoint: `POST /api/v1/cargos/{cargo_id}/pagos`, solo Admin. Montos como texto
exacto en la respuesta y `Decimal` exacto en la base.

Los datos estan elegidos para que un saldo mal calculado de otro numero: en
«Primer pago parcial» la familia tiene otro cargo con un pago (si se ignora
uno de los dos, `saldo_pendiente` no da 70000.00); en «Solo la familia y la
temporada» hay un cargo de la misma familia en la temporada cerrada (sumarlo
da 105000.00) y uno de otra familia en la vigente (sumarlo da 125000.00).
"""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_alumno, crear_cerrada, crear_familia
from tests.functional.pagos.preparacion import es_decimal_exacto
from tests.functional.pagos.preparacion_api import (
    CAMPOS_DE_LA_RESPUESTA,
    admin,
    cuerpo_pago,
    insertar_abono_mes,
    insertar_cargo_fijo,
    insertar_pago_previo,
    nuevo_tipo_fijo,
    pagar,
    pago_por_id,
    pagos_del_cargo,
    preparar_perez,
)


class TestRegistrarUnPago:
    def test_el_primer_pago_parcial_responde_201_con_los_saldos_y_queda_en_la_base(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Primer pago parcial
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # 85000.00, sin pagos
        preinscripcion_ana = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.ana,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
        )
        insertar_pago_previo(sesion, preinscripcion_ana, "5000.00", p.admin)

        respuesta = pagar(
            cliente, admin(cliente), abono, cuerpo_pago("30000.00", date(2026, 11, 2))
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert set(cuerpo) >= CAMPOS_DE_LA_RESPUESTA, cuerpo
        assert cuerpo["cargo_id"] == abono
        assert cuerpo["monto"] == "30000.00"
        assert cuerpo["fecha_pago"] == "2026-11-02"
        assert cuerpo["registrado_por"] == p.admin
        assert cuerpo["registrado_en"]
        assert cuerpo["saldo_cargo"] == "55000.00"
        assert cuerpo["saldo_pendiente"] == "70000.00"

        fila = pago_por_id(sesion, cuerpo["id"])
        assert fila.cargo_id == abono
        es_decimal_exacto(fila.monto, "30000.00")
        assert fila.fecha_pago == date(2026, 11, 2)
        assert fila.registrado_por == p.admin
        assert fila.registrado_en is not None
        assert fila.anulado_en is None
        assert fila.anulado_por is None
        assert fila.motivo_anulacion is None
        assert [f.id for f in pagos_del_cargo(sesion, abono)] == [cuerpo["id"]]

    def test_el_pago_que_completa_el_cargo_deja_saldo_cero_y_dos_pagos_que_suman_el_total(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pagos parciales hasta saldar
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)
        insertar_pago_previo(sesion, abono, "30000.00", p.admin)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("55000.00"))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["saldo_cargo"] == "0.00"
        pagos = pagos_del_cargo(sesion, abono)
        assert len(pagos) == 2
        assert sum((f.monto for f in pagos), Decimal("0.00")) == Decimal("85000.00")
        assert sorted(f.monto for f in pagos) == [Decimal("30000.00"), Decimal("55000.00")]

    def test_un_pago_con_centavos_responde_el_monto_y_el_saldo_con_sus_centavos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Pago con centavos
        p = preparar_perez(sesion)
        materiales = nuevo_tipo_fijo(sesion, p.temporada, "Materiales", "8925.00")
        cargo = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.juan,
            tipo=materiales,
            monto="8925.00",
            creado_por=p.admin,
        )

        respuesta = pagar(cliente, admin(cliente), cargo, cuerpo_pago("4462.50"))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["monto"] == "4462.50"
        assert respuesta.json()["saldo_cargo"] == "4462.50"
        es_decimal_exacto(pago_por_id(sesion, respuesta.json()["id"]).monto, "4462.50")

    def test_un_monto_con_un_solo_decimal_se_responde_con_dos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto con un solo decimal
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("4462.5"))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["monto"] == "4462.50"
        es_decimal_exacto(pago_por_id(sesion, respuesta.json()["id"]).monto, "4462.50")

    def test_el_saldo_pendiente_cuenta_solo_la_familia_y_la_temporada_del_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Solo la familia y la temporada del cargo en el saldo
        p = preparar_perez(sesion)
        abono = insertar_abono_mes(sesion, p)  # 85000.00 de Juan, vigente

        # La misma familia, 30000.00 sin pagos en la temporada cerrada 2025-26.
        cerrada = crear_cerrada(sesion)
        preinscripcion_vieja = nuevo_tipo_fijo(sesion, cerrada, "Preinscripción", "30000.00")
        insertar_cargo_fijo(
            sesion,
            temporada=cerrada,
            familia=p.familia,
            alumno=p.ana,
            tipo=preinscripcion_vieja,
            monto="30000.00",
            creado_por=p.admin,
        )
        # Otra familia, 50000.00 en la temporada vigente.
        gomez = crear_familia(sesion, "socio")
        lucia = crear_alumno(sesion, "Lucía", "Gómez", familia_id=gomez)
        insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=gomez,
            alumno=lucia,
            tipo=nuevo_tipo_fijo(sesion, p.temporada, "Colonia", "50000.00"),
            monto="50000.00",
            creado_por=p.admin,
            categoria="socio",
        )

        respuesta = pagar(cliente, admin(cliente), abono, cuerpo_pago("10000.00"))

        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["saldo_pendiente"] == "75000.00"
