"""Fixtures de los tests.

La base es Postgres de verdad, la misma version mayor que produccion, con
las migraciones aplicadas. No se finge con SQLite: la mitad de los errores
de este sistema son de restricciones, de claves ajenas y de precision
numerica, y nada de eso aparece con otro motor.

El aislamiento es por transaccion. Cada test corre dentro de una
transaccion que se revierte al terminar, asi que ningun test ve lo que
dejo otro y el orden no importa. Es mucho mas rapido que recrear el
esquema por test.
"""

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import obtener_configuracion
from app.core.db import obtener_sesion
from app.main import app

RAIZ = Path(__file__).resolve().parent.parent


def _url_de_pruebas() -> str:
    cfg = obtener_configuracion()
    url = cfg.test_database_url or os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.exit(
            "Falta TEST_DATABASE_URL. Los tests no corren contra la base de "
            "desarrollo: un test que revierte mal te deja sin datos.",
            returncode=1,
        )
    if url == cfg.database_url:
        pytest.exit(
            "TEST_DATABASE_URL es igual a DATABASE_URL. Tienen que ser bases " "distintas.",
            returncode=1,
        )
    return url


@pytest.fixture(scope="session")
def motor_de_pruebas() -> Iterator[object]:
    url = _url_de_pruebas()
    motor = create_engine(url, pool_pre_ping=True)

    # Las migraciones se aplican una vez por sesion de tests, con el mismo
    # comando que produccion. Si una migracion esta rota, los tests no
    # arrancan, que es exactamente lo que queremos.
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=RAIZ,
        env={**os.environ, "ALEMBIC_URL": url},
        check=True,
    )

    yield motor
    motor.dispose()


@pytest.fixture
def conexion(motor_de_pruebas) -> Iterator[Connection]:  # type: ignore[no-untyped-def]
    conexion = motor_de_pruebas.connect()  # type: ignore[attr-defined]
    transaccion = conexion.begin()
    try:
        yield conexion
    finally:
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def sesion(conexion: Connection) -> Iterator[Session]:
    fabrica = sessionmaker(bind=conexion, autoflush=False, expire_on_commit=False)
    s = fabrica(join_transaction_mode="create_savepoint")
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def cliente(sesion: Session) -> Iterator[TestClient]:
    """Cliente de la API atado a la misma transaccion que la fixture `sesion`.

    Los tests comprueban por la API, no llamando a los servicios por dentro:
    lo que se verifica es el contrato. La sesion compartida permite preparar
    el estado con `sesion` y despues leerlo por HTTP.
    """

    def sesion_de_pruebas() -> Iterator[Session]:
        yield sesion

    app.dependency_overrides[obtener_sesion] = sesion_de_pruebas
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def tablas(conexion: Connection) -> list[str]:
    """Las tablas que existen. Util para comprobar que una migracion creo lo
    que decia crear."""
    filas = conexion.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
    )
    return [f[0] for f in filas]
