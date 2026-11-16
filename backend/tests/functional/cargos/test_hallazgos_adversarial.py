"""Capability `cargos`: los Scenarios que agrego el pase adversarial.

Tarea 7.3 de `openspec/changes/cobro/tasks.md`. Un test por Scenario de
`openspec/changes/cobro/specs/cargos/spec.md`:

- «Porcentaje en el límite de 100» (Requirement «El cargo guarda su cálculo»):
  insercion directa en la base, como `test_esquema_cargo.py`. Es el caso de
  adentro del `CHECK` de rango; el de afuera (100.01) ya esta en ese archivo.
- «Descuento del cien por ciento» (Requirement «Un único porcentaje sobre la
  tarifa base»): por la API.
- «Un alumno de otra familia en el mismo turno no cuenta» (Requirement «El
  tramo de hijos del Mes»): por la API, con la tabla de descuentos completa,
  para que el filtro de familia sea lo unico que separa 1 hijo de 2.
- «El repetido llega después de la comprobación previa» (Requirement «Un
  cargo repetido se rechaza»): por la API. Usa el punto de prueba declarado
  en `openspec/changes/cobro/design.md`, seccion «El servicio»: la funcion
  publica `existe_cargo_repetido` de `app.services.cargos`. Es la unica pieza
  interna que este archivo nombra, y la conoce por ese parrafo.

Al final, un CONTROL POSITIVO que tiene que fallar (ver su docstring).
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import crear_familia
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    cargo_de,
    contar_cargos,
    descuento_modalidad,
    descuentos_mes,
    familia_con_hijos,
    hijo_inscripto,
    preparar_vigente,
    tarifa,
)

NO_SOCIO_MES = {1: "0.00", 2: "10.00", 3: "15.00", 4: "20.00"}
REPETIDO_MES_1 = "El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana."

_INSERTAR_CARGO = (
    "INSERT INTO cargo ("
    "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
    "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
    "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
    ") VALUES ("
    ":temporada_id, :familia_id, :alumno_id, :tipo_cargo_id, :inscripcion_id, :modalidad, "
    ":periodo_cobro_id, :fecha_dia, :categoria_aplicada, :cantidad_hijos_aplicada, "
    ":monto_base, :porcentaje_aplicado, :monto_total, :creado_por, now()"
    ")"
)


def _es_decimal_exacto(valor: object, esperado: str) -> None:
    assert isinstance(valor, Decimal), f"Se leyo {type(valor).__name__}, no Decimal"
    assert valor == Decimal(esperado)
    assert valor.as_tuple().exponent == -2, f"{valor} no quedo con dos decimales"


def _cargos_de_la_inscripcion_y_periodo(
    sesion: Session, inscripcion_id: int, periodo_id: int
) -> int:
    return int(
        sesion.execute(
            text("SELECT count(*) FROM cargo WHERE inscripcion_id = :i AND periodo_cobro_id = :p"),
            {"i": inscripcion_id, "p": periodo_id},
        ).scalar_one()
    )


# --- Requirement: El cargo guarda su cálculo ------------------------------------------


class TestElCargoGuardaSuCalculo:
    def test_un_cargo_al_100_por_ciento_con_total_cero_queda_guardado(
        self, sesion: Session
    ) -> None:
        # Scenario: Porcentaje en el límite de 100
        # Un Abono del Dia valido en todo lo demas: Dia con fecha y sin
        # periodo ni cantidad de hijos, total = 8000.00 * (1 - 100/100) = 0.00.
        v = preparar_vigente(sesion)
        familia, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])

        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "temporada_id": v.temporada,
                "familia_id": familia,
                "alumno_id": juan.alumno,
                "tipo_cargo_id": v.abono,
                "inscripcion_id": juan.inscripcion,
                "modalidad": "dia",
                "periodo_cobro_id": None,
                "fecha_dia": date(2027, 1, 5),
                "categoria_aplicada": "empleado",
                "cantidad_hijos_aplicada": None,
                "monto_base": Decimal("8000.00"),
                "porcentaje_aplicado": Decimal("100.00"),
                "monto_total": Decimal("0.00"),
                "creado_por": v.admin,
            },
        )

        fila = sesion.execute(
            text("SELECT monto_base, porcentaje_aplicado, monto_total FROM cargo")
        ).one()
        _es_decimal_exacto(fila.monto_base, "8000.00")
        _es_decimal_exacto(fila.porcentaje_aplicado, "100.00")
        _es_decimal_exacto(fila.monto_total, "0.00")
        assert contar_cargos(sesion) == 1


# --- Requirement: Un único porcentaje sobre la tarifa base ----------------------------


class TestUnUnicoPorcentaje:
    def test_con_descuento_del_100_por_ciento_el_dia_se_registra_con_total_cero(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Descuento del cien por ciento
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "dia", "8000.00")
        descuento_modalidad(sesion, v.temporada, "empleado", "dia", "100.00")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, juan, "dia", fecha_dia="2027-01-05")
        )

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["porcentaje_aplicado"] == "100.00"
        assert cuerpo["monto_total"] == "0.00"
        fila = sesion.execute(
            text("SELECT porcentaje_aplicado, monto_total FROM cargo WHERE inscripcion_id = :i"),
            {"i": juan.inscripcion},
        ).one()
        _es_decimal_exacto(fila.porcentaje_aplicado, "100.00")
        _es_decimal_exacto(fila.monto_total, "0.00")


# --- Requirement: El tramo de hijos del Mes ---------------------------------------------


class TestElTramoDeHijosDelMes:
    def test_un_alumno_de_otra_familia_en_el_mismo_grupo_y_turno_no_suma_al_tramo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Un alumno de otra familia en el mismo turno no cuenta
        # La tabla completa: si Sofia contara, el tramo 2 existe (10.00) y el
        # total seria 90000.00. El filtro de familia es lo unico que lo separa.
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "no_socio", NO_SOCIO_MES)
        _, (juan,) = familia_con_hijos(sesion, v, "no_socio", ["Juan"])
        # Sofia: otra familia, la misma categoria, inscripta en «Delfines» manana.
        otra_familia = crear_familia(sesion, "no_socio")
        hijo_inscripto(sesion, v, otra_familia, "Sofía", "Gómez", turno="manana")
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["cantidad_hijos_aplicada"] == 1
        assert cuerpo["monto_total"] == "100000.00"
        fila = cargo_de(sesion, juan.inscripcion, v.mes_1)
        assert fila.cantidad_hijos_aplicada == 1
        _es_decimal_exacto(fila.monto_total, "100000.00")


# --- Requirement: Un cargo repetido se rechaza --------------------------------------------


class TestElRepetidoDespuesDeLaComprobacion:
    def test_el_repetido_que_choca_con_el_indice_unico_responde_409_y_no_500(
        self, cliente: TestClient, sesion: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Scenario: El repetido llega después de la comprobación previa
        # El otro pedido ya guardo el cargo (insercion directa); este paso la
        # comprobacion previa (reemplazada por una que dice «no hay repetido»,
        # punto de prueba declarado en el design) y llega al INSERT.
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "15.00"})
        familia, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "temporada_id": v.temporada,
                "familia_id": familia,
                "alumno_id": juan.alumno,
                "tipo_cargo_id": v.abono,
                "inscripcion_id": juan.inscripcion,
                "modalidad": "mes",
                "periodo_cobro_id": v.mes_1,
                "fecha_dia": None,
                "categoria_aplicada": "empleado",
                "cantidad_hijos_aplicada": 1,
                "monto_base": Decimal("100000.00"),
                "porcentaje_aplicado": Decimal("15.00"),
                "monto_total": Decimal("85000.00"),
                "creado_por": v.admin,
            },
        )
        monkeypatch.setattr("app.services.cargos.existe_cargo_repetido", lambda *a, **k: False)
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == REPETIDO_MES_1
        assert _cargos_de_la_inscripcion_y_periodo(sesion, juan.inscripcion, v.mes_1) == 1
