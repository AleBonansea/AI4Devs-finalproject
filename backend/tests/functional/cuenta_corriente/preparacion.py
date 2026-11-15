"""Preparacion compartida de los tests de `GET /api/v1/familias/{familia_id}/cuenta-corriente`.

No es un archivo de tests (pytest no lo junta: no empieza con `test_`).

La familia «Pérez – Ana» y sus cargos salen de `pagos/preparacion_api.py`
(temporada vigente 2026-27, Admin `mgarcia`, Ana 2018 y Juan 2020, Juan en
«Delfines» manana, «Mes 1» del 2027-01-04 al 2027-01-29, tipos «Abono» y
«Preinscripción»). Aca se agrega lo que esos helpers no tienen: Juan en un
grupo de la tarde, el «Abono» del Dia con fecha, y un «Abono» del Mes de un
alumno de otra familia. Todo insertado directo en `cargo`, coherente con sus
`CHECK` (Dia: sin periodo ni cantidad de hijos, con fecha; Mes: con periodo
y cantidad de hijos; total = base * (1 - porcentaje / 100)).

Los archivos de `pagos/`, `cargos/` y `asistencia/` no se tocan: de ahi solo
se importa.
"""

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.functional.asistencia.preparacion import inscribir, insertar_grupo
from tests.functional.pagos.preparacion_api import Perez

MENSAJE_FAMILIA_INEXISTENTE = "La familia no existe."
MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."
ID_INEXISTENTE = 999999
ID_FUERA_DE_RANGO = 9223372036854775808

CAMPOS_DEL_CARGO = {
    "id",
    "alumno_id",
    "nombre",
    "apellido",
    "tipo_cargo",
    "modalidad",
    "turno",
    "periodo",
    "fecha_dia",
    "monto_total",
    "pagado",
    "saldo",
    "creado_en",
    "pagos",
}
CAMPOS_DEL_PAGO = {"id", "monto", "fecha_pago"}
CAMPOS_DE_LA_FAMILIA = {
    "familia_id",
    "etiqueta",
    "categoria",
    "total_cargos",
    "total_pagado",
    "saldo_pendiente",
    "cargos",
}


def url_cuenta_corriente(familia_id: int | str) -> str:
    return f"/api/v1/familias/{familia_id}/cuenta-corriente"


def pedir(
    cliente: TestClient, encabezados: dict[str, str] | None, familia_id: int | str
) -> Response:
    return cliente.get(url_cuenta_corriente(familia_id), headers=encabezados)


def pedir_200(
    cliente: TestClient, encabezados: dict[str, str], familia_id: int | str
) -> dict[str, Any]:
    respuesta = pedir(cliente, encabezados, familia_id)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo: dict[str, Any] = respuesta.json()
    return cuerpo


def cargo_de(cuerpo: dict[str, Any], cargo_id: int) -> dict[str, Any]:
    """El cargo con ese id en la respuesta; falla si no esta o esta repetido."""
    encontrados = [c for c in cuerpo["cargos"] if c["id"] == cargo_id]
    assert len(encontrados) == 1, cuerpo["cargos"]
    return encontrados[0]


# --- cargos que los helpers de pagos no tienen ------------------------------------

_INSERTAR_CARGO = (
    "INSERT INTO cargo ("
    "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
    "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
    "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
    ") VALUES ("
    ":t, :f, :a, :tc, :i, :mod, :p, :fd, :c, :h, :base, :pct, :total, :u, now()"
    ") RETURNING id"
)


def inscribir_juan_a_la_tarde(sesion: Session, p: Perez) -> int:
    """Juan inscripto tambien en «Pulpos» tarde de la vigente. Devuelve la inscripcion."""
    pulpos = insertar_grupo(sesion, p.temporada, "Pulpos", "tarde")
    return inscribir(sesion, p.juan, pulpos, p.temporada, "tarde", p.admin)


def insertar_abono_dia(
    sesion: Session,
    p: Perez,
    inscripcion: int,
    fecha: date,
    *,
    base: str = "10000.00",
    porcentaje: str = "10.00",
    total: str = "9000.00",
) -> int:
    """El «Abono» del Dia de Juan en `fecha`, sobre `inscripcion`. Por
    defecto 10000.00 al 10 %: 9000.00. Sin periodo ni cantidad de hijos."""
    return int(
        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "t": p.temporada,
                "f": p.familia,
                "a": p.juan,
                "tc": p.abono,
                "i": inscripcion,
                "mod": "dia",
                "p": None,
                "fd": fecha,
                "c": "empleado",
                "h": None,
                "base": Decimal(base),
                "pct": Decimal(porcentaje),
                "total": Decimal(total),
                "u": p.admin,
            },
        ).scalar_one()
    )


def insertar_abono_mes_de_otro(
    sesion: Session,
    p: Perez,
    *,
    familia: int,
    alumno: int,
    inscripcion: int,
    categoria: str,
    base: str,
    porcentaje: str,
    total: str,
) -> int:
    """Un «Abono» del Mes, «Mes 1», de un alumno de otra familia en la
    vigente de `p`, con un hijo en el turno."""
    return int(
        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "t": p.temporada,
                "f": familia,
                "a": alumno,
                "tc": p.abono,
                "i": inscripcion,
                "mod": "mes",
                "p": p.mes_1,
                "fd": None,
                "c": categoria,
                "h": 1,
                "base": Decimal(base),
                "pct": Decimal(porcentaje),
                "total": Decimal(total),
                "u": p.admin,
            },
        ).scalar_one()
    )
