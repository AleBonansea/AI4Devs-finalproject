"""El saldo de un cargo, en un solo lugar.

`pagado_por_cargo()` es el subselect que suma los pagos no anulados de cada
cargo; lo usan `saldo_de_cargos` y, después, la cuenta corriente, para que
nunca diverjan.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Subquery, Text, cast, func, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session

from app.models.alumno import Alumno, Inscripcion
from app.models.cargo import Cargo
from app.models.cuenta_corriente import v_cuenta_corriente
from app.models.familia import Familia, v_familia_etiqueta
from app.models.pago import Pago
from app.models.tarifario import PeriodoCobro, TipoCargo
from app.models.temporada import EstadoTemporada, Temporada
from app.schemas.cuenta_corriente import (
    CargoEnCuenta,
    CuentaCorriente,
    PagoEnCuenta,
    PeriodoDeCargo,
)
from app.services.comunes import id_posible
from app.services.familias import MENSAJE_FAMILIA_INEXISTENTE, FamiliaInexistente

_CENTAVO = Decimal("0.01")


def pagado_por_cargo() -> Subquery:
    """`cargo_id` y `pagado` (suma de los pagos no anulados), agrupado por cargo."""
    consulta = (
        select(Pago.cargo_id.label("cargo_id"), func.sum(Pago.monto).label("pagado"))
        .where(Pago.anulado_en.is_(None))
        .group_by(Pago.cargo_id)
    )
    return consulta.subquery("pagado_por_cargo")


def saldo_de_cargos(sesion: Session, cargo_ids: Sequence[int]) -> dict[int, Decimal]:
    """Lo que falta pagar de cada cargo: total menos pagos no anulados."""
    pagado = pagado_por_cargo()
    filas = sesion.execute(
        select(Cargo.id, Cargo.monto_total - func.coalesce(pagado.c.pagado, 0))
        .outerjoin(pagado, pagado.c.cargo_id == Cargo.id)
        .where(Cargo.id.in_(cargo_ids))
    ).all()
    return {cargo_id: Decimal(saldo).quantize(_CENTAVO) for cargo_id, saldo in filas}


def saldo_de_familia(sesion: Session, familia_id: int, temporada_id: int) -> Decimal:
    """El saldo pendiente de la familia en la temporada, desde `v_cuenta_corriente`.

    Sin cargos no hay fila en la vista: el saldo es 0.
    """
    saldo = sesion.execute(
        select(func.coalesce(v_cuenta_corriente.c.saldo_pendiente, 0)).where(
            v_cuenta_corriente.c.familia_id == familia_id,
            v_cuenta_corriente.c.temporada_id == temporada_id,
        )
    ).scalar_one_or_none()
    return Decimal(saldo or 0).quantize(_CENTAVO)


def obtener_cuenta_corriente(sesion: Session, familia_id: int) -> CuentaCorriente:
    """Cargos y pagos de la familia en la temporada vigente, con sus saldos.

    Una sola sentencia (cargos, pagos agregados y totales): ve una sola foto de
    la base. Nada se suma en Python: `pagado` y `saldo` salen del mismo subselect
    que usa `registrar_pago` y los totales, de `v_cuenta_corriente`.
    """
    if not id_posible(familia_id):
        raise FamiliaInexistente(MENSAJE_FAMILIA_INEXISTENTE)
    familia = sesion.execute(
        select(Familia.categoria, v_familia_etiqueta.c.etiqueta)
        .join(v_familia_etiqueta, v_familia_etiqueta.c.familia_id == Familia.id)
        .where(Familia.id == familia_id)
    ).one_or_none()
    if familia is None:
        raise FamiliaInexistente(MENSAJE_FAMILIA_INEXISTENTE)

    pagado = pagado_por_cargo()
    # Los pagos no anulados de cada cargo, en una lista JSON ordenada. Monto y
    # fecha viajan como texto: un monto dentro de un JSON no pasa por `float`.
    pagos_agregados = (
        select(
            Pago.cargo_id.label("cargo_id"),
            func.json_agg(
                aggregate_order_by(
                    func.json_build_object(
                        "id",
                        Pago.id,
                        "monto",
                        cast(Pago.monto, Text),
                        "fecha_pago",
                        cast(Pago.fecha_pago, Text),
                    ),
                    Pago.fecha_pago,
                    Pago.id,
                )
            ).label("pagos"),
        )
        .where(Pago.anulado_en.is_(None))
        .group_by(Pago.cargo_id)
        .cte("pagos_agregados")
    )
    totales = (
        select(
            v_cuenta_corriente.c.temporada_id,
            v_cuenta_corriente.c.total_cargos,
            v_cuenta_corriente.c.total_pagos,
            v_cuenta_corriente.c.saldo_pendiente,
        )
        .where(v_cuenta_corriente.c.familia_id == familia_id)
        .cte("totales")
    )
    # Una sola sentencia: una sola foto de la base, aunque se commitee un pago
    # mientras tanto. Los totales se repiten en cada fila.
    filas = sesion.execute(
        select(
            Cargo,
            Alumno.nombre,
            Alumno.apellido,
            TipoCargo.nombre.label("tipo_cargo"),
            Inscripcion.turno,
            PeriodoCobro.nombre.label("periodo_nombre"),
            PeriodoCobro.fecha_desde,
            PeriodoCobro.fecha_hasta,
            func.coalesce(pagado.c.pagado, 0).label("pagado"),
            (Cargo.monto_total - func.coalesce(pagado.c.pagado, 0)).label("saldo"),
            pagos_agregados.c.pagos,
            func.coalesce(totales.c.total_cargos, 0).label("total_cargos"),
            func.coalesce(totales.c.total_pagos, 0).label("total_pagos"),
            func.coalesce(totales.c.saldo_pendiente, 0).label("saldo_pendiente"),
        )
        .join(Temporada, Temporada.id == Cargo.temporada_id)
        .join(Alumno, Alumno.id == Cargo.alumno_id)
        .join(TipoCargo, TipoCargo.id == Cargo.tipo_cargo_id)
        .outerjoin(Inscripcion, Inscripcion.id == Cargo.inscripcion_id)
        .outerjoin(PeriodoCobro, PeriodoCobro.id == Cargo.periodo_cobro_id)
        .outerjoin(pagado, pagado.c.cargo_id == Cargo.id)
        .outerjoin(pagos_agregados, pagos_agregados.c.cargo_id == Cargo.id)
        .outerjoin(totales, totales.c.temporada_id == Cargo.temporada_id)
        .where(Cargo.familia_id == familia_id, Temporada.estado == EstadoTemporada.VIGENTE)
        .order_by(Cargo.creado_en, Cargo.id)
    ).all()
    # Sin cargos no hay filas ni fila en la vista: los totales son 0.
    total_cargos, total_pagado, saldo_pendiente = (
        (filas[0].total_cargos, filas[0].total_pagos, filas[0].saldo_pendiente)
        if filas
        else (0, 0, 0)
    )

    cargos = [
        CargoEnCuenta(
            id=fila.Cargo.id,
            alumno_id=fila.Cargo.alumno_id,
            nombre=fila.nombre,
            apellido=fila.apellido,
            tipo_cargo=fila.tipo_cargo,
            modalidad=fila.Cargo.modalidad,
            turno=fila.turno,
            periodo=(
                PeriodoDeCargo(
                    nombre=fila.periodo_nombre,
                    fecha_desde=fila.fecha_desde,
                    fecha_hasta=fila.fecha_hasta,
                )
                if fila.periodo_nombre is not None
                else None
            ),
            fecha_dia=fila.Cargo.fecha_dia,
            monto_total=fila.Cargo.monto_total,
            pagado=Decimal(fila.pagado).quantize(_CENTAVO),
            saldo=Decimal(fila.saldo).quantize(_CENTAVO),
            creado_en=fila.Cargo.creado_en,
            pagos=[PagoEnCuenta.model_validate(pago) for pago in fila.pagos or []],
        )
        for fila in filas
    ]
    return CuentaCorriente(
        familia_id=familia_id,
        etiqueta=familia.etiqueta,
        categoria=familia.categoria,
        total_cargos=Decimal(total_cargos).quantize(_CENTAVO),
        total_pagado=Decimal(total_pagado).quantize(_CENTAVO),
        saldo_pendiente=Decimal(saldo_pendiente).quantize(_CENTAVO),
        cargos=cargos,
    )
