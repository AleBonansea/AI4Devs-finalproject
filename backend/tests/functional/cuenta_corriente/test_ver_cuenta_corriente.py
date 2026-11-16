"""Capability `cuenta-corriente`: ver la cuenta corriente de una familia
(change cuenta-corriente, tarea 3.1).

Un test por Scenario del Requirement «Ver la cuenta corriente de una
familia», en `openspec/changes/cuenta-corriente/specs/cuenta-corriente/spec.md`.

Endpoint: `GET /api/v1/familias/{familia_id}/cuenta-corriente`, solo Admin.

Orden: los cargos del mas antiguo al mas nuevo (`creado_en` y despues `id`;
dentro de un test todos tienen el mismo `creado_en`, asi que manda el orden
de insercion). Los pagos, por `fecha_pago` y despues `id`.

Datos elegidos para que un orden equivocado se note:
- «El detalle de cada cargo»: los cargos se insertan Preinscripción (20000),
  Abono del Mes (85000), Abono del Dia (9000). Ordenar por monto, por nombre
  del tipo o por modalidad da otro orden. Los pagos del Mes se insertan el
  del 2026-11-05 antes que el del 2026-11-02: ordenar por id los invierte.
- «Solo la temporada vigente»: sumar el cargo de la cerrada da 115000.00.
- «Solo los cargos de esa familia»: sumar el de Lucía da 175000.00 de
  cargos; sus pagos, 30000.00 pagados.
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import (
    crear_alumno,
    crear_cerrada,
    crear_familia,
    inscribir,
)
from tests.functional.cuenta_corriente.preparacion import (
    CAMPOS_DE_LA_FAMILIA,
    CAMPOS_DEL_CARGO,
    CAMPOS_DEL_PAGO,
    ID_FUERA_DE_RANGO,
    ID_INEXISTENTE,
    MENSAJE_FAMILIA_INEXISTENTE,
    cargo_de,
    inscribir_juan_a_la_tarde,
    insertar_abono_dia,
    insertar_abono_mes_de_otro,
    pedir,
    pedir_200,
)
from tests.functional.pagos.preparacion_api import (
    admin,
    insertar_abono_mes,
    insertar_cargo_fijo,
    insertar_pago_previo,
    nuevo_tipo_fijo,
    preparar_perez,
)


class TestVerLaCuentaCorrienteDeUnaFamilia:
    def test_trae_la_familia_y_sus_tres_cargos_en_orden_con_su_detalle(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: El detalle de cada cargo
        p = preparar_perez(sesion)  # «Pérez – Ana», empleado
        juan_tarde = inscribir_juan_a_la_tarde(sesion, p)
        preinscripcion = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.ana,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
        )
        mes = insertar_abono_mes(sesion, p)  # Juan, manana, «Mes 1», 85000.00
        pago_del_5 = insertar_pago_previo(sesion, mes, "10000.00", p.admin, fecha=date(2026, 11, 5))
        pago_del_2 = insertar_pago_previo(sesion, mes, "30000.00", p.admin, fecha=date(2026, 11, 2))
        dia = insertar_abono_dia(sesion, p, juan_tarde, date(2027, 1, 8))  # 9000.00

        respuesta = pedir(cliente, admin(cliente), p.familia)

        assert respuesta.status_code == 200, respuesta.text
        cuerpo = respuesta.json()
        assert set(cuerpo) >= CAMPOS_DE_LA_FAMILIA
        assert cuerpo["familia_id"] == p.familia
        assert cuerpo["etiqueta"] == "Pérez – Ana"
        assert cuerpo["categoria"] == "empleado"
        assert [c["id"] for c in cuerpo["cargos"]] == [preinscripcion, mes, dia]

        de_la_preinscripcion, del_mes, del_dia = cuerpo["cargos"]

        assert de_la_preinscripcion["tipo_cargo"] == "Preinscripción"
        assert de_la_preinscripcion["alumno_id"] == p.ana
        assert de_la_preinscripcion["nombre"] == "Ana"
        assert de_la_preinscripcion["apellido"] == "Pérez"
        assert de_la_preinscripcion["monto_total"] == "20000.00"
        assert de_la_preinscripcion["modalidad"] is None
        assert de_la_preinscripcion["turno"] is None
        assert de_la_preinscripcion["periodo"] is None
        assert de_la_preinscripcion["fecha_dia"] is None
        assert de_la_preinscripcion["pagos"] == []

        assert del_mes["tipo_cargo"] == "Abono"
        assert del_mes["alumno_id"] == p.juan
        assert del_mes["nombre"] == "Juan"
        assert del_mes["monto_total"] == "85000.00"
        assert del_mes["modalidad"] == "mes"
        assert del_mes["turno"] == "manana"
        assert del_mes["periodo"]["nombre"] == "Mes 1"
        assert del_mes["periodo"]["fecha_desde"] == "2027-01-04"
        assert del_mes["periodo"]["fecha_hasta"] == "2027-01-29"
        assert del_mes["fecha_dia"] is None
        assert del_mes["pagos"] == [
            {"id": pago_del_2, "monto": "30000.00", "fecha_pago": "2026-11-02"},
            {"id": pago_del_5, "monto": "10000.00", "fecha_pago": "2026-11-05"},
        ]
        for pago in del_mes["pagos"]:
            assert set(pago) == CAMPOS_DEL_PAGO

        assert del_dia["tipo_cargo"] == "Abono"
        assert del_dia["nombre"] == "Juan"
        assert del_dia["monto_total"] == "9000.00"
        assert del_dia["modalidad"] == "dia"
        assert del_dia["turno"] == "tarde"
        assert del_dia["periodo"] is None
        assert del_dia["fecha_dia"] == "2027-01-08"

    def test_trae_solo_los_cargos_de_la_temporada_vigente(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Solo la temporada vigente
        p = preparar_perez(sesion)
        vigente = insertar_abono_mes(sesion, p)  # 85000.00
        cerrada = crear_cerrada(sesion)
        insertar_cargo_fijo(
            sesion,
            temporada=cerrada,
            familia=p.familia,
            alumno=p.ana,
            tipo=nuevo_tipo_fijo(sesion, cerrada, "Preinscripción", "30000.00"),
            monto="30000.00",
            creado_por=p.admin,
        )

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert [(c["id"], c["monto_total"]) for c in cuerpo["cargos"]] == [(vigente, "85000.00")]
        assert cuerpo["total_cargos"] == "85000.00"
        assert cuerpo["saldo_pendiente"] == "85000.00"

    def test_no_trae_el_cargo_de_otra_familia_ni_lo_suma(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Solo los cargos de esa familia
        p = preparar_perez(sesion)
        de_juan = insertar_abono_mes(sesion, p)  # 85000.00, Delfines manana
        insertar_pago_previo(sesion, de_juan, "10000.00", p.admin)
        gomez = crear_familia(sesion, "socio")
        lucia = crear_alumno(
            sesion, "Lucía", "Gómez", familia_id=gomez, nacimiento=date(2019, 6, 1)
        )
        lucia_en_delfines = inscribir(sesion, lucia, p.delfines, p.temporada, "manana", p.admin)
        de_lucia = insertar_abono_mes_de_otro(
            sesion,
            p,
            familia=gomez,
            alumno=lucia,
            inscripcion=lucia_en_delfines,
            categoria="socio",
            base="100000.00",
            porcentaje="10.00",
            total="90000.00",
        )
        insertar_pago_previo(sesion, de_lucia, "20000.00", p.admin)

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert [c["id"] for c in cuerpo["cargos"]] == [de_juan]
        assert cuerpo["total_cargos"] == "85000.00"
        assert cuerpo["total_pagado"] == "10000.00"
        assert cuerpo["saldo_pendiente"] == "75000.00"
        texto = str(cuerpo)
        assert "Lucía" not in texto
        assert "Gómez" not in texto

    def test_una_familia_sin_cargos_en_la_temporada_da_lista_vacia_y_totales_en_cero(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Familia sin cargos en la temporada
        # Juan esta inscripto en «Delfines» manana. Hay un cargo de otra
        # familia en la vigente: una consulta sin filtro por familia lo traeria.
        p = preparar_perez(sesion)
        gomez = crear_familia(sesion, "socio")
        lucia = crear_alumno(sesion, "Lucía", "Gómez", familia_id=gomez)
        insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=gomez,
            alumno=lucia,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
            categoria="socio",
        )

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert cuerpo["familia_id"] == p.familia
        assert cuerpo["cargos"] == []
        assert cuerpo["total_cargos"] == "0.00"
        assert cuerpo["total_pagado"] == "0.00"
        assert cuerpo["saldo_pendiente"] == "0.00"

    def test_cada_cargo_tiene_exactamente_los_catorce_campos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Sin datos médicos ni de personas
        p = preparar_perez(sesion)
        cargo = insertar_abono_mes(sesion, p)  # de Juan
        insertar_pago_previo(sesion, cargo, "30000.00", p.admin)

        cuerpo = pedir_200(cliente, admin(cliente), p.familia)

        assert len(cuerpo["cargos"]) == 1
        for elemento in cuerpo["cargos"]:
            assert set(elemento) == CAMPOS_DEL_CARGO
        assert cargo_de(cuerpo, cargo)["alumno_id"] == p.juan

    def test_una_familia_que_no_existe_da_404(self, cliente: TestClient, sesion: Session) -> None:
        # Scenario: Familia que no existe
        p = preparar_perez(sesion)
        assert p.familia != ID_INEXISTENTE

        respuesta = pedir(cliente, admin(cliente), ID_INEXISTENTE)

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FAMILIA_INEXISTENTE

    def test_un_id_mas_grande_que_el_maximo_da_404(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Id de familia más grande que el máximo
        preparar_perez(sesion)

        respuesta = pedir(cliente, admin(cliente), ID_FUERA_DE_RANGO)

        assert respuesta.status_code == 404, respuesta.text
        assert respuesta.json()["detail"] == MENSAJE_FAMILIA_INEXISTENTE
