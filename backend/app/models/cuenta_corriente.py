"""La vista `v_cuenta_corriente`: una sola definicion del saldo de una familia.

Va sobre `metadata_vistas`, igual que `v_familia_etiqueta`: la crea y la
borra la migracion con SQL escrito a mano. Una familia sin cargos en la
temporada no tiene fila: quien la consulta usa `coalesce(..., 0)`.
"""

from sqlalchemy import BigInteger, Column, Numeric, Table

from app.models.base import metadata_vistas

v_cuenta_corriente = Table(
    "v_cuenta_corriente",
    metadata_vistas,
    Column("familia_id", BigInteger, primary_key=True),
    Column("temporada_id", BigInteger, primary_key=True),
    Column("total_cargos", Numeric(12, 2)),
    Column("total_pagos", Numeric(12, 2)),
    Column("saldo_pendiente", Numeric(12, 2)),
)
