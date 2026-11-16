"""Preparacion compartida de los tests de `POST /api/v1/cargos/{cargo_id}/pagos`.

No es un archivo de tests (pytest no lo junta: no empieza con `test_`). Lo
usan `pagos/test_registrar_pago.py`, `pagos/test_saldo_del_cargo.py`,
`pagos/test_monto_y_fecha_pago.py`, `pagos/test_cargo_del_pago.py`,
`pagos/test_permisos_pago.py` y `tesoreria/test_ingreso_por_pago.py`.

Temporadas, usuarios, familias, alumnos, grupos e inscripciones salen de
`asistencia/preparacion.py`; periodos y tipos de cargo, de
`cargos/preparacion.py`. Los cargos «ya registrados» se insertan directo en
`cargo`, coherentes con sus `CHECK`; los pagos previos y los anulados, directo
en `pago` (los anulados con sus tres datos de anulacion).

`pagos/preparacion.py` esta congelado y no se toca: de ahi solo se importa.

La familia «Pérez – Ana»: Ana es la mayor (2018) y Juan el menor (2020),
inscripto en «Delfines» manana de la temporada vigente 2026-27.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    crear_alumno,
    crear_familia,
    crear_usuario,
    crear_vigente,
    errores_con_loc_terminado_en,
    ingresar,
    inscribir,
    insertar_grupo,
)
from tests.functional.cargos.preparacion import periodo, tipo_cargo
from tests.functional.pagos.preparacion import INSERTAR_PAGO, contar

MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."
MENSAJE_SUPERA_SALDO = "El monto supera el saldo del cargo."
MENSAJE_SALDADO = "El cargo ya está saldado."
MENSAJE_FORMATO_MONTO = "Tiene que ser un monto con hasta dos decimales."
MENSAJE_MAYOR_QUE_CERO = "Tiene que ser mayor que cero."
MENSAJE_FECHA_FUTURA = "La fecha del pago no puede ser posterior a hoy."
MENSAJE_OBLIGATORIO = "Este dato es obligatorio."
MENSAJE_CARGO_INEXISTENTE = "El cargo no existe."
MENSAJE_TEMPORADA_CERRADA = "El cargo es de una temporada cerrada, que queda solo para consulta."

# Un id que ninguna tabla de la base de pruebas alcanza, y otro fuera de bigint.
ID_INEXISTENTE = 999999
ID_FUERA_DE_RANGO = 9223372036854775808

# La fecha de pago de los Scenarios que no hablan de la fecha: anterior a hoy.
FECHA_PAGO = date(2026, 11, 2)

CAMPOS_DE_LA_RESPUESTA = {
    "id",
    "cargo_id",
    "monto",
    "fecha_pago",
    "registrado_por",
    "registrado_en",
    "saldo_cargo",
    "saldo_pendiente",
}


def url_pagos(cargo_id: int | str) -> str:
    return f"/api/v1/cargos/{cargo_id}/pagos"


# --- la familia «Pérez – Ana» en la temporada vigente ---------------------------


@dataclass(frozen=True)
class Perez:
    """La temporada vigente 2026-27, el Admin `mgarcia`, la familia «Pérez –
    Ana» (empleado) con Ana y Juan, Juan inscripto en «Delfines» manana, el
    periodo «Mes 1» y los tipos «Abono» (tarifario) y «Preinscripción»
    (monto fijo 20000.00). Sin cargos ni pagos."""

    temporada: int
    admin: int
    familia: int
    ana: int
    juan: int
    delfines: int
    inscripcion_juan: int
    mes_1: int
    abono: int
    preinscripcion: int


def preparar_perez(sesion: Session) -> Perez:
    temporada = crear_vigente(sesion)
    admin = crear_usuario(sesion, "mgarcia", RolUsuario.ADMIN)
    familia = crear_familia(sesion, "empleado")
    ana = crear_alumno(sesion, "Ana", "Pérez", familia_id=familia, nacimiento=date(2018, 5, 2))
    juan = crear_alumno(sesion, "Juan", "Pérez", familia_id=familia, nacimiento=date(2020, 3, 10))
    delfines = insertar_grupo(sesion, temporada, "Delfines", "manana")
    return Perez(
        temporada=temporada,
        admin=admin,
        familia=familia,
        ana=ana,
        juan=juan,
        delfines=delfines,
        inscripcion_juan=inscribir(sesion, juan, delfines, temporada, "manana", admin),
        mes_1=periodo(sesion, temporada, "mes", "Mes 1", date(2027, 1, 4), date(2027, 1, 29)),
        abono=tipo_cargo(sesion, temporada, "Abono", "tarifario", None),
        preinscripcion=tipo_cargo(sesion, temporada, "Preinscripción", "monto_fijo", "20000.00"),
    )


# --- cargos ya registrados, insertados directo ----------------------------------

_INSERTAR_CARGO = (
    "INSERT INTO cargo ("
    "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
    "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
    "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
    ") VALUES ("
    ":t, :f, :a, :tc, :i, :mod, :p, NULL, :c, :h, :base, :pct, :total, :u, now()"
    ") RETURNING id"
)


def insertar_abono_mes(
    sesion: Session,
    p: Perez,
    *,
    base: str = "100000.00",
    porcentaje: str = "15.00",
    total: str = "85000.00",
) -> int:
    """El «Abono» del Mes de Juan, «Mes 1», manana. Por defecto, 100000.00
    al 15 %: 85000.00. `total` tiene que ser coherente con base y porcentaje."""
    return int(
        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "t": p.temporada,
                "f": p.familia,
                "a": p.juan,
                "tc": p.abono,
                "i": p.inscripcion_juan,
                "mod": "mes",
                "p": p.mes_1,
                "c": "empleado",
                "h": 1,
                "base": Decimal(base),
                "pct": Decimal(porcentaje),
                "total": Decimal(total),
                "u": p.admin,
            },
        ).scalar_one()
    )


def insertar_cargo_fijo(
    sesion: Session,
    *,
    temporada: int,
    familia: int,
    alumno: int,
    tipo: int,
    monto: str,
    creado_por: int,
    categoria: str = "empleado",
) -> int:
    """Un cargo de monto fijo sin descuento: sin inscripcion, modalidad,
    periodo ni cantidad de hijos, total = base."""
    return int(
        sesion.execute(
            text(_INSERTAR_CARGO),
            {
                "t": temporada,
                "f": familia,
                "a": alumno,
                "tc": tipo,
                "i": None,
                "mod": None,
                "p": None,
                "c": categoria,
                "h": None,
                "base": Decimal(monto),
                "pct": Decimal("0.00"),
                "total": Decimal(monto),
                "u": creado_por,
            },
        ).scalar_one()
    )


def nuevo_tipo_fijo(sesion: Session, temporada: int, nombre: str, monto: str) -> int:
    return tipo_cargo(sesion, temporada, nombre, "monto_fijo", monto)


# --- pagos previos, insertados directo ------------------------------------------


def insertar_pago_previo(
    sesion: Session,
    cargo: int,
    monto: str,
    registrado_por: int,
    *,
    fecha: date = FECHA_PAGO,
    anulado: bool = False,
) -> int:
    """Un pago «ya registrado». Si `anulado`, con sus tres datos de anulacion
    completos (momento, autor y motivo)."""
    return int(
        sesion.execute(
            text(INSERTAR_PAGO),
            {
                "cargo_id": cargo,
                "monto": Decimal(monto),
                "fecha_pago": fecha,
                "registrado_por": registrado_por,
                "anulado_en": datetime(2026, 11, 3, 12, 0, tzinfo=UTC) if anulado else None,
                "anulado_por": registrado_por if anulado else None,
                "motivo_anulacion": "Cargado por error" if anulado else None,
            },
        ).scalar_one()
    )


# --- conteos y lecturas de la base ---------------------------------------------


def contar_pagos(sesion: Session) -> int:
    return contar(sesion, "pago")


def contar_movimientos(sesion: Session) -> int:
    return contar(sesion, "tesoreria_movimiento")


def pagos_del_cargo(sesion: Session, cargo: int) -> list[Any]:
    return list(
        sesion.execute(
            text(
                "SELECT id, cargo_id, monto, fecha_pago, registrado_por, registrado_en, "
                "anulado_en, anulado_por, motivo_anulacion "
                "FROM pago WHERE cargo_id = :c ORDER BY id"
            ),
            {"c": cargo},
        ).all()
    )


def pago_por_id(sesion: Session, pago_id: int) -> Any:
    return sesion.execute(
        text(
            "SELECT id, cargo_id, monto, fecha_pago, registrado_por, registrado_en, "
            "anulado_en, anulado_por, motivo_anulacion FROM pago WHERE id = :id"
        ),
        {"id": pago_id},
    ).one()


def movimientos(sesion: Session) -> list[Any]:
    return list(
        sesion.execute(
            text(
                "SELECT id, temporada_id, tipo::text AS tipo, origen::text AS origen, pago_id, "
                "descripcion, monto, fecha, registrado_por "
                "FROM tesoreria_movimiento ORDER BY id"
            )
        ).all()
    )


# --- pedidos ---------------------------------------------------------------------


def cuerpo_pago(monto: Any, fecha: date = FECHA_PAGO) -> dict[str, Any]:
    return {"monto": monto, "fecha_pago": fecha.isoformat()}


def admin(cliente: TestClient) -> dict[str, str]:
    return ingresar(cliente, "mgarcia")


def pagar(
    cliente: TestClient, encabezados: dict[str, str] | None, cargo: int | str, cuerpo: Any
) -> Response:
    return cliente.post(url_pagos(cargo), headers=encabezados, json=cuerpo)


def pagar_201(
    cliente: TestClient, encabezados: dict[str, str], cargo: int, cuerpo: Any
) -> dict[str, Any]:
    """Paga y exige el 201: para los Scenarios donde un pago es un paso y no
    lo que se prueba."""
    respuesta = pagar(cliente, encabezados, cargo, cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    datos: dict[str, Any] = respuesta.json()
    return datos


# --- rechazos --------------------------------------------------------------------


def exigir_error_en(respuesta: Response, campo: str, mensaje: str) -> list[dict[str, Any]]:
    """Exige un 422 con `detail` lista y, entre los errores cuyo `loc`
    termina en `campo`, uno con `msg` igual a `mensaje`. Devuelve los errores
    de ese campo."""
    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    errores = errores_con_loc_terminado_en(respuesta, campo)
    assert mensaje in [e["msg"] for e in errores], detalle
    return errores
