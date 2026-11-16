"""Piezas compartidas por los servicios."""

# Tope de las columnas BIGINT. Un id mas grande hacia fallar a Postgres y
# respondia 500; se trata como inexistente.
_ID_MAXIMO = 2**63 - 1


def id_posible(valor: int) -> bool:
    """El id cabe en una columna BIGINT y es positivo."""
    return 1 <= valor <= _ID_MAXIMO
