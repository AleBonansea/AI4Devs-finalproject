"""Capability `cargos`: un cargo repetido se rechaza.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirement «Un cargo repetido se rechaza», mas el test de la carrera que
pide la tarea 3.2 de `openspec/changes/cobro/tasks.md`.

La carrera (dos pedidos iguales que pasan los dos la comprobacion y chocan
en el `INSERT`) no se puede provocar desde un test de API. Lo que si se
puede afirmar desde afuera: con el mismo cargo ya presente en la base,
insertado directo con SQL y no por la API, el registro responde 409 con el
mensaje de la spec, y nunca 500.
"""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import inscribir
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    contar_cargos,
    descuento_modalidad,
    descuentos_mes,
    familia_con_hijos,
    preinscripcion,
    preparar_vigente,
    registrar,
    tarifa,
)

REPETIDO_MES_1 = "El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana."


def cargos_de_la_inscripcion_y_periodo(
    sesion: Session, inscripcion_id: int, periodo_id: int
) -> int:
    return int(
        sesion.execute(
            text("SELECT count(*) FROM cargo WHERE inscripcion_id = :i AND periodo_cobro_id = :p"),
            {"i": inscripcion_id, "p": periodo_id},
        ).scalar_one()
    )


class TestUnCargoRepetidoSeRechaza:
    def test_el_mismo_abono_del_mes_dos_veces_responde_409_y_queda_un_solo_cargo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El mismo Abono del Mes dos veces
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        registrar(cliente, encabezados, abono_mes(v, juan))

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == REPETIDO_MES_1
        assert cargos_de_la_inscripcion_y_periodo(sesion, juan.inscripcion, v.mes_1) == 1
        assert contar_cargos(sesion) == 1

    def test_el_mismo_periodo_en_el_otro_turno_se_registra(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El mismo período en el otro turno
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        tarifa(sesion, v.temporada, "tarde", "mes", "80000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "10.00", 2: "15.00"})
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        inscripcion_tarde = inscribir(sesion, juan.alumno, v.pulpos, v.temporada, "tarde", v.admin)
        encabezados = admin(cliente)
        registrar(cliente, encabezados, abono_mes(v, juan))
        cuerpo_tarde = abono_mes(v, juan)
        cuerpo_tarde["inscripcion_id"] = inscripcion_tarde

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo_tarde)

        assert respuesta.status_code == 201, respuesta.text
        assert contar_cargos(sesion) == 2

    def test_el_mismo_dia_dos_veces_responde_409_con_la_fecha_y_el_turno(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El mismo Día dos veces
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "dia", "8000.00")
        descuento_modalidad(sesion, v.temporada, "empleado", "dia", "10.00")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        cuerpo = abono(v, juan, "dia", fecha_dia="2027-01-05")
        registrar(cliente, encabezados, cuerpo)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo)

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == (
            "El alumno ya tiene un cargo «Abono» del día 05/01/2027 en el turno mañana."
        )
        assert contar_cargos(sesion) == 1

    def test_dos_preinscripciones_del_mismo_alumno_responden_409(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Dos Preinscripciones del mismo alumno
        v = preparar_vigente(sesion)
        _, (juan,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)
        registrar(cliente, encabezados, preinscripcion(v, juan.alumno))

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=preinscripcion(v, juan.alumno)
        )

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == (
            "El alumno ya tiene un cargo «Preinscripción» en esta temporada."
        )
        assert contar_cargos(sesion) == 1


class TestLaCarreraDelRepetido:
    def test_un_cargo_ya_insertado_en_la_base_da_409_y_no_500(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Tarea 3.2: el mismo cargo ya ocupa el indice unico, puesto con SQL
        # directo y no por la API. Registrarlo responde el 409 de la spec.
        v = preparar_vigente(sesion)
        tarifa(sesion, v.temporada, "manana", "mes", "100000.00")
        descuentos_mes(sesion, v.temporada, "empleado", {1: "15.00"})
        familia, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        sesion.execute(
            text(
                "INSERT INTO cargo ("
                "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
                "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
                "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
                ") VALUES ("
                ":t, :f, :a, :tc, :i, 'mes', :p, NULL, 'empleado', 1, "
                ":base, :pct, :total, :u, now())"
            ),
            {
                "t": v.temporada,
                "f": familia,
                "a": juan.alumno,
                "tc": v.abono,
                "i": juan.inscripcion,
                "p": v.mes_1,
                "base": Decimal("100000.00"),
                "pct": Decimal("15.00"),
                "total": Decimal("85000.00"),
                "u": v.admin,
            },
        )
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono_mes(v, juan))

        assert respuesta.status_code == 409, respuesta.text
        assert respuesta.json()["detail"] == REPETIDO_MES_1
        assert cargos_de_la_inscripcion_y_periodo(sesion, juan.inscripcion, v.mes_1) == 1
