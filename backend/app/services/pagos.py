"""Registrar un pago.

Orden fijo (design, «El servicio de pagos»); el rol y el cuerpo ya los
resolvió FastAPI:
  3. el cargo existe (bloqueado con FOR UPDATE)
  4. su temporada no está cerrada -> 409
  5. saldo del cargo: saldado -> 409; monto mayor -> 422
  6. INSERT del pago y de su ingreso en tesorería
  7. saldos de la respuesta y un solo commit
"""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errores import ReglaIncumplida
from app.models.cargo import Cargo
from app.models.cuenta_corriente import v_cuenta_corriente
from app.models.enums import OrigenMovimiento, TipoMovimiento
from app.models.pago import Pago
from app.models.temporada import EstadoTemporada, Temporada
from app.models.tesoreria import TesoreriaMovimiento
from app.models.usuario import Usuario
from app.schemas.pagos import PagoEntrada, PagoRegistrado
from app.services.comunes import id_posible
from app.services.cuenta_corriente import saldo_de_cargos

MENSAJE_CARGO_INEXISTENTE = "El cargo no existe."
MENSAJE_CARGO_SALDADO = "El cargo ya está saldado."
MENSAJE_TEMPORADA_CERRADA = "El cargo es de una temporada cerrada, que queda solo para consulta."
MENSAJE_SUPERA_SALDO = "El monto supera el saldo del cargo."


class ConflictoDePago(Exception):
    """Un 409 (saldado o temporada cerrada). El mensaje es el texto final."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class CargoInexistente(Exception):
    """Un 404: el cargo no existe."""


def registrar_pago(
    sesion: Session, usuario: Usuario, cargo_id: int, entrada: PagoEntrada
) -> PagoRegistrado:
    monto = Decimal(entrada.monto)
    cargo = (
        sesion.execute(
            select(Cargo).where(Cargo.id == cargo_id).with_for_update()
        ).scalar_one_or_none()
        if id_posible(cargo_id)
        else None
    )
    if cargo is None:
        raise CargoInexistente(MENSAJE_CARGO_INEXISTENTE)

    # Acl. 10 (la temporada anterior queda «solo para consulta») y
    # `3-modelo-de-datos.md`, «`temporada`»: la API rechaza altas en tablas que
    # cuelgan de una temporada cerrada.
    temporada = sesion.get(Temporada, cargo.temporada_id)
    if temporada is None or temporada.estado is EstadoTemporada.CERRADA:
        raise ConflictoDePago(MENSAJE_TEMPORADA_CERRADA)

    saldo = saldo_de_cargos(sesion, [cargo.id])[cargo.id]
    if saldo <= 0:
        raise ConflictoDePago(MENSAJE_CARGO_SALDADO)
    if monto > saldo:
        raise ReglaIncumplida([(("monto",), MENSAJE_SUPERA_SALDO)])

    pago = Pago(
        cargo_id=cargo.id,
        monto=monto,
        fecha_pago=entrada.fecha_pago,
        registrado_por=usuario.id,
    )
    sesion.add(pago)
    sesion.flush()
    sesion.add(
        TesoreriaMovimiento(
            temporada_id=cargo.temporada_id,
            tipo=TipoMovimiento.INGRESO,
            origen=OrigenMovimiento.PAGO,
            pago_id=pago.id,
            monto=monto,
            fecha=entrada.fecha_pago,
            registrado_por=usuario.id,
        )
    )
    sesion.flush()

    # Se vuelve a consultar (ya ve el pago nuevo): restar en Python sería un
    # segundo cálculo del saldo.
    saldo_cargo = saldo_de_cargos(sesion, [cargo.id])[cargo.id]
    # El de la familia sale de la vista; sin cargos no hay fila (acá siempre hay una).
    saldo_pendiente = Decimal(
        sesion.execute(
            select(func.coalesce(v_cuenta_corriente.c.saldo_pendiente, 0)).where(
                v_cuenta_corriente.c.familia_id == cargo.familia_id,
                v_cuenta_corriente.c.temporada_id == cargo.temporada_id,
            )
        ).scalar_one()
    ).quantize(Decimal("0.01"))
    sesion.commit()
    return PagoRegistrado(
        id=pago.id,
        cargo_id=pago.cargo_id,
        monto=pago.monto,
        fecha_pago=pago.fecha_pago,
        registrado_por=pago.registrado_por,
        registrado_en=pago.registrado_en,
        saldo_cargo=saldo_cargo,
        saldo_pendiente=saldo_pendiente,
    )
