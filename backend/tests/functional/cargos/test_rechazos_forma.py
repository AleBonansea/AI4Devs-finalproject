"""Capability `cargos`: qué pide cada tipo de cargo.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`,
Requirement «Qué pide cada tipo de cargo».

En cada test el resto del pedido es valido y el tarifario esta completo:
el unico error que puede aparecer es el del Scenario. Cuando el Scenario
pide varios errores, se exigen todos en la misma respuesta. Y en cada
rechazo se cuenta que no quedo ningun cargo en la base.
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import inscribir
from tests.functional.cargos.preparacion import (
    URL_CARGOS,
    abono,
    abono_mes,
    admin,
    contar_cargos,
    familia_con_hijos,
    periodo,
    preparar_cerrada,
    preparar_vigente,
)
from tests.functional.cargos.rechazos import ID_INEXISTENTE, exigir_rechazo, tarifario_completo

OBLIGATORIO = "Este dato es obligatorio."
NO_LLEVA = "Un cargo de monto fijo no lleva este dato."


class TestQuePideCadaTipoDeCargo:
    def test_alumno_y_tipo_de_cargo_inexistentes_dan_un_error_en_cada_campo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Alumno y tipo de cargo que no existen
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json={"alumno_id": ID_INEXISTENTE, "tipo_cargo_id": ID_INEXISTENTE},
        )

        exigir_rechazo(
            respuesta,
            {
                "alumno_id": "El alumno no existe.",
                "tipo_cargo_id": "El tipo de cargo no existe.",
            },
        )
        assert contar_cargos(sesion) == 0

    def test_el_monto_fijo_con_datos_del_abono_da_un_error_en_cada_dato_y_no_guarda(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Monto fijo con datos del Abono
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "socio")
        _, (juan,) = familia_con_hijos(sesion, v, "socio", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json={
                "alumno_id": juan.alumno,
                "tipo_cargo_id": v.preinscripcion,
                "inscripcion_id": juan.inscripcion,
                "modalidad": "mes",
                "periodo_cobro_id": v.mes_1,
            },
        )

        exigir_rechazo(
            respuesta,
            {"inscripcion_id": NO_LLEVA, "modalidad": NO_LLEVA, "periodo_cobro_id": NO_LLEVA},
        )
        assert contar_cargos(sesion) == 0

    def test_el_abono_sin_inscripcion_ni_modalidad_da_obligatorio_en_los_dos(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Abono sin inscripción ni modalidad
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json={"alumno_id": juan.alumno, "tipo_cargo_id": v.abono},
        )

        exigir_rechazo(respuesta, {"inscripcion_id": OBLIGATORIO, "modalidad": OBLIGATORIO})
        assert contar_cargos(sesion) == 0

    def test_la_inscripcion_de_otro_alumno_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Inscripción de otro alumno
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        _, (sofia,) = familia_con_hijos(sesion, v, "empleado", ["Sofía"])
        encabezados = admin(cliente)
        cuerpo = abono_mes(v, juan)
        cuerpo["inscripcion_id"] = sofia.inscripcion

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo)

        exigir_rechazo(respuesta, {"inscripcion_id": "La inscripción no es del alumno."})
        assert contar_cargos(sesion) == 0

    def test_una_inscripcion_que_no_existe_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Inscripción que no existe
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)
        cuerpo = abono_mes(v, juan)
        cuerpo["inscripcion_id"] = ID_INEXISTENTE

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo)

        exigir_rechazo(respuesta, {"inscripcion_id": "La inscripción no existe."})
        assert contar_cargos(sesion) == 0

    def test_una_inscripcion_de_otra_temporada_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Inscripción de otra temporada
        # Juan tambien esta inscripto en 2026-27, para que el unico error
        # sea el de la inscripcion y no el de «no está inscripto en la
        # temporada».
        v = preparar_vigente(sesion)
        c = preparar_cerrada(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        inscripcion_cerrada = inscribir(
            sesion, juan.alumno, c.delfines, c.temporada, "manana", v.admin
        )
        encabezados = admin(cliente)
        cuerpo = abono_mes(v, juan)
        cuerpo["inscripcion_id"] = inscripcion_cerrada

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo)

        exigir_rechazo(
            respuesta,
            {"inscripcion_id": "La inscripción no es de la temporada del tipo de cargo."},
        )
        assert contar_cargos(sesion) == 0

    def test_el_mes_sin_periodo_da_obligatorio_en_el_periodo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Mes sin período
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=abono(v, juan, "mes"))

        exigir_rechazo(respuesta, {"periodo_cobro_id": OBLIGATORIO})
        assert contar_cargos(sesion) == 0

    def test_un_periodo_de_otra_modalidad_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Período de otra modalidad
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, juan, "mes", periodo_id=v.semana_1)
        )

        exigir_rechazo(respuesta, {"periodo_cobro_id": "El período es de otra modalidad."})
        assert contar_cargos(sesion) == 0

    def test_un_periodo_que_no_existe_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Período que no existe
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json=abono(v, juan, "mes", periodo_id=ID_INEXISTENTE),
        )

        exigir_rechazo(respuesta, {"periodo_cobro_id": "El período no existe."})
        assert contar_cargos(sesion) == 0

    def test_un_periodo_de_otra_temporada_se_rechaza(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Período de otra temporada
        v = preparar_vigente(sesion)
        c = preparar_cerrada(sesion)
        mes_1_cerrada = periodo(
            sesion, c.temporada, "mes", "Mes 1", date(2026, 1, 5), date(2026, 1, 30)
        )
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono_mes(v, juan, mes_1_cerrada)
        )

        exigir_rechazo(
            respuesta,
            {"periodo_cobro_id": "El período no es de la temporada del tipo de cargo."},
        )
        assert contar_cargos(sesion) == 0

    def test_la_semana_con_fecha_se_rechaza_en_la_fecha(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Semana con fecha
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS,
            headers=encabezados,
            json=abono(v, juan, "semana", periodo_id=v.semana_1, fecha_dia="2027-01-05"),
        )

        exigir_rechazo(respuesta, {"fecha_dia": "Solo la modalidad Día lleva fecha."})
        assert contar_cargos(sesion) == 0

    def test_el_dia_sin_fecha_y_con_periodo_da_un_error_en_cada_campo(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Día sin fecha y con período
        v = preparar_vigente(sesion)
        tarifario_completo(sesion, v.temporada, "empleado")
        _, (juan,) = familia_con_hijos(sesion, v, "empleado", ["Juan"])
        encabezados = admin(cliente)

        respuesta = cliente.post(
            URL_CARGOS, headers=encabezados, json=abono(v, juan, "dia", periodo_id=v.semana_1)
        )

        exigir_rechazo(
            respuesta,
            {
                "fecha_dia": OBLIGATORIO,
                "periodo_cobro_id": "La modalidad Día no lleva período.",
            },
        )
        assert contar_cargos(sesion) == 0
