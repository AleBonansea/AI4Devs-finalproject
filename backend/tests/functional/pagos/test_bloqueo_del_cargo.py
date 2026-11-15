"""Capability `pagos`: dos pagos simultaneos del mismo cargo (change
cuenta-corriente, tarea 7.3).

Scenario «Dos pagos simultáneos del mismo cargo», del Requirement «Un pago no
supera el saldo del cargo» de
`openspec/changes/cuenta-corriente/specs/pagos/spec.md`.

La carrera no se puede provocar desde aca: cada test corre en una sola
transaccion y la API comparte esa conexion (`conftest.py`, fixtures
`conexion` y `cliente`), asi que dos pedidos nunca compiten de verdad. Por eso
este test se apoya en el punto de prueba declarado en
`openspec/changes/cuenta-corriente/design.md`, «El servicio de pagos», parrafo
«El bloqueo del cargo es un punto de prueba declarado»: durante un `POST`
valido, el `SELECT` sobre `cargo` lleva `FOR UPDATE`.

**Este test conoce esa pieza interna solo por ese parrafo del design**, no
por haber leido el servicio. Si el bloqueo se cambia por otro mecanismo, este
test tiene que cambiarse a proposito. La carrera real se comprobo a mano
(tarea 6.1: uno 201 y otro 409).

El listener `before_cursor_execute` se registra sobre la conexion de la
fixture `conexion`, que es la misma que usa la sesion de la API en los tests,
y solo alrededor del `POST`: lo que prepara el test y el ingreso del Admin no
entran en la captura. Se retira en un `finally`, tambien si el pedido falla.

Ademas del bloqueo se exige el 201 y un solo pago del cargo: sin eso, un
pedido que fallara antes de llegar a la base dejaria la afirmacion del
`FOR UPDATE` sin sentido.
"""

import re
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Connection, event
from sqlalchemy.orm import Session

from tests.functional.pagos.preparacion_api import (
    admin,
    cuerpo_pago,
    insertar_cargo_fijo,
    pagar,
    pagos_del_cargo,
    preparar_perez,
)

# Un SELECT cuyo FROM nombra la tabla `cargo` (con o sin comillas), seguida de
# espacio o fin. `FROM tipo_cargo` no matchea: exige `from`, espacios y el
# nombre exacto.
_SELECT_DE_CARGO = re.compile(r'^\s*select\b.*\bfrom\s+"?cargo"?(\s|$)', re.IGNORECASE | re.DOTALL)
_FOR_UPDATE = re.compile(r"\bfor\s+update\b", re.IGNORECASE)


def _es_select_de_cargo_con_for_update(sentencia: str) -> bool:
    return bool(_SELECT_DE_CARGO.search(sentencia)) and bool(_FOR_UPDATE.search(sentencia))


def _pagar_capturando_sentencias(
    conexion: Connection, cliente: TestClient, encabezados: dict[str, str], cargo: int
) -> tuple[Any, list[str]]:
    """Hace el `POST` del pago y devuelve la respuesta y las sentencias SQL
    ejecutadas durante el pedido, en orden."""
    sentencias: list[str] = []

    def capturar(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        sentencias.append(statement)

    event.listen(conexion, "before_cursor_execute", capturar)
    try:
        respuesta = pagar(cliente, encabezados, cargo, cuerpo_pago("20000.00"))
    finally:
        event.remove(conexion, "before_cursor_execute", capturar)
    return respuesta, sentencias


class TestUnPagoNoSuperaElSaldoDelCargo:
    def test_el_select_del_cargo_bloquea_la_fila_con_for_update(
        self, conexion: Connection, cliente: TestClient, sesion: Session
    ) -> None:
        # Scenario: Dos pagos simultáneos del mismo cargo
        p = preparar_perez(sesion)
        preinscripcion = insertar_cargo_fijo(
            sesion,
            temporada=p.temporada,
            familia=p.familia,
            alumno=p.ana,
            tipo=p.preinscripcion,
            monto="20000.00",
            creado_por=p.admin,
        )
        encabezados = admin(cliente)

        respuesta, sentencias = _pagar_capturando_sentencias(
            conexion, cliente, encabezados, preinscripcion
        )

        assert respuesta.status_code == 201, respuesta.text
        assert len(pagos_del_cargo(sesion, preinscripcion)) == 1
        assert sentencias, "El pedido no ejecutó ninguna sentencia en la conexión observada."
        assert any(_es_select_de_cargo_con_for_update(s) for s in sentencias), (
            "Ningún SELECT sobre `cargo` llevó FOR UPDATE. Sentencias sobre cargo: "
            + repr([s for s in sentencias if _SELECT_DE_CARGO.search(s)])
        )
