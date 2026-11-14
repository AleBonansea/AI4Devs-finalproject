"""Preparacion compartida de los tests de los endpoints de cargos.

No es un archivo de tests (pytest no lo junta: no empieza con `test_`). Lo
usan `test_registrar.py`, `test_calculo_por_api.py`, `test_simular.py` y
`test_permisos.py`.

Temporadas, usuarios, grupos, alumnos e inscripciones salen de
`asistencia/preparacion.py`, igual que en `test_esquema_cargo.py`. El
tarifario NO sale de la semilla: cada test carga las tarifas y los
porcentajes de su Scenario con las funciones de aca (los porcentajes de la
semilla son otros, y un test que dependiera de ellos probaria la semilla).

Cuando un Scenario arranca con un cargo «ya registrado» que no es lo que se
prueba (la Preinscripcion de Ana del saldo, el cargo de otra temporada), se
inserta directo en `cargo`, con un total coherente con el `CHECK`.

Fechas de las temporadas, las de la spec:
- vigente 2026-27: del 2027-01-04 al 2027-02-26;
- cerrada 2025-26: del 2026-01-05 al 2026-02-27.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RolUsuario
from tests.functional.asistencia.preparacion import (
    crear_alumno,
    crear_cerrada,
    crear_familia,
    crear_usuario,
    crear_vigente,
    ingresar,
    inscribir,
    insertar_grupo,
)

URL_CARGOS = "/api/v1/cargos"
URL_SIMULACION = "/api/v1/cargos/simulacion"
MENSAJE_SIN_PERMISO = "No tenés permiso para esta operación."

CAMPOS_DE_MONTO = {"monto_base", "porcentaje_aplicado", "monto_total", "saldo_pendiente"}


# --- tarifario ---------------------------------------------------------------


def tarifa(sesion: Session, temporada_id: int, turno: str, modalidad: str, monto: str) -> None:
    sesion.execute(
        text(
            "INSERT INTO tarifa_base (temporada_id, turno, modalidad, monto) "
            "VALUES (:t, :turno, :m, :monto)"
        ),
        {"t": temporada_id, "turno": turno, "m": modalidad, "monto": Decimal(monto)},
    )


def descuento_modalidad(
    sesion: Session, temporada_id: int, categoria: str, modalidad: str, porcentaje: str
) -> None:
    sesion.execute(
        text(
            "INSERT INTO descuento_modalidad (temporada_id, categoria, modalidad, porcentaje) "
            "VALUES (:t, :c, :m, :p)"
        ),
        {"t": temporada_id, "c": categoria, "m": modalidad, "p": Decimal(porcentaje)},
    )


def descuentos_mes(
    sesion: Session, temporada_id: int, categoria: str, por_tramo: dict[int, str]
) -> None:
    """Una fila de `descuento_mes` por tramo: `{1: "10.00", 2: "15.00", ...}`."""
    for tramo, porcentaje in por_tramo.items():
        sesion.execute(
            text(
                "INSERT INTO descuento_mes (temporada_id, categoria, tramo_hijos, porcentaje) "
                "VALUES (:t, :c, :tramo, :p)"
            ),
            {"t": temporada_id, "c": categoria, "tramo": tramo, "p": Decimal(porcentaje)},
        )


def todos_los_descuentos(
    sesion: Session, temporada_id: int, categoria: str, porcentaje: str
) -> None:
    """La categoria con el mismo porcentaje en Dia, Semana, Quincena y los
    cuatro tramos del Mes."""
    for modalidad in ("dia", "semana", "quincena"):
        descuento_modalidad(sesion, temporada_id, categoria, modalidad, porcentaje)
    descuentos_mes(sesion, temporada_id, categoria, {t: porcentaje for t in (1, 2, 3, 4)})


def periodo(
    sesion: Session, temporada_id: int, modalidad: str, nombre: str, desde: date, hasta: date
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO periodo_cobro "
                "(temporada_id, modalidad, nombre, fecha_desde, fecha_hasta) "
                "VALUES (:t, :m, :n, :d, :h) RETURNING id"
            ),
            {"t": temporada_id, "m": modalidad, "n": nombre, "d": desde, "h": hasta},
        ).scalar_one()
    )


def tipo_cargo(
    sesion: Session, temporada_id: int, nombre: str, calculo: str, monto_fijo: str | None
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO tipo_cargo (temporada_id, nombre, calculo, monto_fijo) "
                "VALUES (:t, :n, :c, :m) RETURNING id"
            ),
            {
                "t": temporada_id,
                "n": nombre,
                "c": calculo,
                "m": Decimal(monto_fijo) if monto_fijo is not None else None,
            },
        ).scalar_one()
    )


# --- la temporada vigente con lo comun a todos los Scenarios -------------------


@dataclass(frozen=True)
class Vigente:
    """La temporada 2026-27 con un Admin (`mgarcia`), los grupos «Delfines»
    manana y «Pulpos» tarde, los periodos «Mes 1», «Mes 2», «Quincena 1» y
    «Semana 1», y los tipos «Abono» (tarifario) y «Preinscripción» (monto
    fijo 20000.00). Sin tarifas ni descuentos: los pone cada test."""

    temporada: int
    admin: int
    delfines: int
    pulpos: int
    mes_1: int
    mes_2: int
    quincena_1: int
    semana_1: int
    abono: int
    preinscripcion: int


def preparar_vigente(sesion: Session) -> Vigente:
    temporada = crear_vigente(sesion)
    return Vigente(
        temporada=temporada,
        admin=crear_usuario(sesion, "mgarcia", RolUsuario.ADMIN),
        delfines=insertar_grupo(sesion, temporada, "Delfines", "manana"),
        pulpos=insertar_grupo(sesion, temporada, "Pulpos", "tarde"),
        mes_1=periodo(sesion, temporada, "mes", "Mes 1", date(2027, 1, 4), date(2027, 1, 29)),
        mes_2=periodo(sesion, temporada, "mes", "Mes 2", date(2027, 2, 1), date(2027, 2, 26)),
        quincena_1=periodo(
            sesion, temporada, "quincena", "Quincena 1", date(2027, 1, 4), date(2027, 1, 15)
        ),
        semana_1=periodo(
            sesion, temporada, "semana", "Semana 1", date(2027, 1, 4), date(2027, 1, 8)
        ),
        abono=tipo_cargo(sesion, temporada, "Abono", "tarifario", None),
        preinscripcion=tipo_cargo(sesion, temporada, "Preinscripción", "monto_fijo", "20000.00"),
    )


@dataclass(frozen=True)
class Cerrada:
    """La temporada 2025-26, cerrada, con el grupo «Delfines» manana."""

    temporada: int
    delfines: int


def preparar_cerrada(sesion: Session) -> Cerrada:
    temporada = crear_cerrada(sesion)
    return Cerrada(
        temporada=temporada,
        delfines=insertar_grupo(sesion, temporada, "Delfines", "manana"),
    )


def grupo_del_turno(v: Vigente, turno: str) -> int:
    return v.delfines if turno == "manana" else v.pulpos


@dataclass(frozen=True)
class Hijo:
    alumno: int
    inscripcion: int


def hijo_inscripto(
    sesion: Session,
    v: Vigente,
    familia_id: int,
    nombre: str,
    apellido: str = "Pérez",
    *,
    turno: str = "manana",
    nacimiento: date = date(2019, 3, 10),
) -> Hijo:
    """Un alumno de la familia, inscripto en 2026-27 en el grupo del turno."""
    alumno = crear_alumno(sesion, nombre, apellido, familia_id=familia_id, nacimiento=nacimiento)
    inscripcion = inscribir(sesion, alumno, grupo_del_turno(v, turno), v.temporada, turno, v.admin)
    return Hijo(alumno=alumno, inscripcion=inscripcion)


def familia_con_hijos(
    sesion: Session, v: Vigente, categoria: str, nombres: list[str], *, turno: str = "manana"
) -> tuple[int, list[Hijo]]:
    """Una familia de la categoria con un hijo por nombre, todos inscriptos en
    el mismo turno de 2026-27. El primero es el mayor."""
    familia = crear_familia(sesion, categoria)
    hijos = [
        hijo_inscripto(sesion, v, familia, nombre, turno=turno, nacimiento=date(2017 + i, 3, 10))
        for i, nombre in enumerate(nombres)
    ]
    return familia, hijos


# --- cargos ya registrados, insertados directo -----------------------------------


def insertar_cargo_monto_fijo(
    sesion: Session,
    *,
    temporada_id: int,
    familia_id: int,
    alumno_id: int,
    tipo_cargo_id: int,
    categoria: str,
    monto: str,
    creado_por: int,
) -> None:
    """Un cargo de monto fijo sin descuento, ya registrado. Total = base."""
    sesion.execute(
        text(
            "INSERT INTO cargo ("
            "temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, modalidad, "
            "periodo_cobro_id, fecha_dia, categoria_aplicada, cantidad_hijos_aplicada, "
            "monto_base, porcentaje_aplicado, monto_total, creado_por, creado_en"
            ") VALUES ("
            ":t, :f, :a, :tc, NULL, NULL, NULL, NULL, :c, NULL, :m, 0, :m, :u, now())"
        ),
        {
            "t": temporada_id,
            "f": familia_id,
            "a": alumno_id,
            "tc": tipo_cargo_id,
            "c": categoria,
            "m": Decimal(monto),
            "u": creado_por,
        },
    )


def contar_cargos(sesion: Session) -> int:
    return int(sesion.execute(text("SELECT count(*) FROM cargo")).scalar_one())


def cargo_en_la_base(sesion: Session, cargo_id: int) -> Any:
    return sesion.execute(
        text(
            "SELECT temporada_id, familia_id, alumno_id, tipo_cargo_id, inscripcion_id, "
            "modalidad::text AS modalidad, periodo_cobro_id, fecha_dia, "
            "categoria_aplicada::text AS categoria_aplicada, cantidad_hijos_aplicada, "
            "monto_base, porcentaje_aplicado, monto_total, creado_por "
            "FROM cargo WHERE id = :id"
        ),
        {"id": cargo_id},
    ).one()


def cargo_de(sesion: Session, inscripcion_id: int, periodo_id: int) -> Any:
    return sesion.execute(
        text(
            "SELECT cantidad_hijos_aplicada, monto_base, porcentaje_aplicado, monto_total "
            "FROM cargo WHERE inscripcion_id = :i AND periodo_cobro_id = :p"
        ),
        {"i": inscripcion_id, "p": periodo_id},
    ).one()


# --- cuerpos y pedidos -------------------------------------------------------------


def abono(
    v: Vigente,
    hijo: Hijo,
    modalidad: str,
    *,
    periodo_id: int | None = None,
    fecha_dia: str | None = None,
) -> dict[str, Any]:
    """Cuerpo de un «Abono»: solo las claves que la modalidad lleva."""
    cuerpo: dict[str, Any] = {
        "alumno_id": hijo.alumno,
        "tipo_cargo_id": v.abono,
        "inscripcion_id": hijo.inscripcion,
        "modalidad": modalidad,
    }
    if periodo_id is not None:
        cuerpo["periodo_cobro_id"] = periodo_id
    if fecha_dia is not None:
        cuerpo["fecha_dia"] = fecha_dia
    return cuerpo


def abono_mes(v: Vigente, hijo: Hijo, periodo_id: int | None = None) -> dict[str, Any]:
    return abono(v, hijo, "mes", periodo_id=periodo_id if periodo_id is not None else v.mes_1)


def preinscripcion(v: Vigente, alumno_id: int) -> dict[str, Any]:
    """Cuerpo de una «Preinscripción»: sin inscripcion, modalidad, periodo ni fecha."""
    return {"alumno_id": alumno_id, "tipo_cargo_id": v.preinscripcion}


def admin(cliente: TestClient) -> dict[str, str]:
    return ingresar(cliente, "mgarcia")


def registrar(
    cliente: TestClient, encabezados: dict[str, str], cuerpo: dict[str, Any]
) -> dict[str, Any]:
    """Registra y exige el 201: para los Scenarios donde registrar no es lo
    que se prueba sino la preparacion o uno de varios pasos."""
    respuesta = cliente.post(URL_CARGOS, headers=encabezados, json=cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    cuerpo_respuesta: dict[str, Any] = respuesta.json()
    return cuerpo_respuesta


def errores_con_loc_terminado_en(respuesta: Any, campo: str) -> list[dict[str, Any]]:
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    return [e for e in detalle if list(e["loc"])[-1:] == [campo]]
