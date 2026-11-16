"""Capability `cargos`: opciones para registrar un cargo.

Un test por Scenario de `openspec/changes/cobro/specs/cargos/spec.md`:
- Requirement «Opciones para registrar un cargo», Scenario «Tipos y
  períodos de la temporada vigente»;
- Requirement «Solo el Admin registra cargos», Scenario «Coordinador pide
  las opciones».

La temporada se arma aca y no con `preparar_vigente`, que trae «Quincena 1»
y otro orden de insercion. El orden de insercion esta elegido para que
ningun orden equivocado coincida con el pedido:
- «Preinscripción» antes que «Abono»: el orden por id no es el orden por
  nombre;
- «Semana 1» antes que «Mes 1», y los dos del 2027-01-04: ordenar solo por
  fecha (y luego id) pondria «Semana 1» primero;
- «Mes 2» antes que «Mes 1»: el orden por id no es el orden por fecha.
"""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    crear_cerrada,
    crear_usuario,
    crear_vigente,
    ingresar,
)
from tests.functional.cargos.preparacion import periodo, tipo_cargo

URL_OPCIONES = "/api/v1/cargos/opciones"


class TestOpcionesParaRegistrarUnCargo:
    def test_trae_tipos_por_nombre_y_periodos_por_modalidad_y_fecha_solo_de_la_vigente(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Tipos y períodos de la temporada vigente
        cerrada = crear_cerrada(sesion)
        tipo_cargo(sesion, cerrada, "Abono", "tarifario", None)
        periodo(sesion, cerrada, "mes", "Mes 1", date(2026, 1, 5), date(2026, 1, 30))

        vigente = crear_vigente(sesion)
        preinscripcion = tipo_cargo(sesion, vigente, "Preinscripción", "monto_fijo", "20000.00")
        abono = tipo_cargo(sesion, vigente, "Abono", "tarifario", None)
        semana_1 = periodo(
            sesion, vigente, "semana", "Semana 1", date(2027, 1, 4), date(2027, 1, 8)
        )
        mes_2 = periodo(sesion, vigente, "mes", "Mes 2", date(2027, 2, 1), date(2027, 2, 26))
        mes_1 = periodo(sesion, vigente, "mes", "Mes 1", date(2027, 1, 4), date(2027, 1, 29))

        crear_usuario(sesion, "mgarcia", RolUsuario.ADMIN)
        encabezados = ingresar(cliente, "mgarcia")

        respuesta = cliente.get(URL_OPCIONES, headers=encabezados)

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json() == {
            "tipos_cargo": [
                {"id": abono, "nombre": "Abono", "calculo": "tarifario", "monto_fijo": None},
                {
                    "id": preinscripcion,
                    "nombre": "Preinscripción",
                    "calculo": "monto_fijo",
                    "monto_fijo": "20000.00",
                },
            ],
            "periodos": [
                {
                    "id": mes_1,
                    "modalidad": "mes",
                    "nombre": "Mes 1",
                    "fecha_desde": "2027-01-04",
                    "fecha_hasta": "2027-01-29",
                },
                {
                    "id": mes_2,
                    "modalidad": "mes",
                    "nombre": "Mes 2",
                    "fecha_desde": "2027-02-01",
                    "fecha_hasta": "2027-02-26",
                },
                {
                    "id": semana_1,
                    "modalidad": "semana",
                    "nombre": "Semana 1",
                    "fecha_desde": "2027-01-04",
                    "fecha_hasta": "2027-01-08",
                },
            ],
        }


class TestSoloElAdminPideLasOpciones:
    def test_el_coordinador_que_pide_las_opciones_recibe_403(
        self, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Coordinador pide las opciones
        vigente = crear_vigente(sesion)
        tipo_cargo(sesion, vigente, "Abono", "tarifario", None)
        periodo(sesion, vigente, "mes", "Mes 1", date(2027, 1, 4), date(2027, 1, 29))
        crear_usuario(sesion, "lrodriguez", RolUsuario.COORDINADOR)
        encabezados = ingresar(cliente, "lrodriguez")

        respuesta = cliente.get(URL_OPCIONES, headers=encabezados)

        assert respuesta.status_code == 403, respuesta.text
