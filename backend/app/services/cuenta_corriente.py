"""El saldo de un cargo, en un solo lugar.

`pagado_por_cargo()` es el subselect que suma los pagos no anulados de cada
cargo; lo usan `saldo_de_cargos` y, después, la cuenta corriente, para que
nunca diverjan.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Subquery, func, select
from sqlalchemy.orm import Session

from app.models.cargo import Cargo
from app.models.pago import Pago

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
