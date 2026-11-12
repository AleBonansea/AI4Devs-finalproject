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
from httpx import Response
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
    """La sesion del TEST, para preparar el estado y comprobarlo despues.

    La API no la usa: tiene la suya (ver `cliente`).
    """
    fabrica = sessionmaker(bind=conexion, autoflush=False, expire_on_commit=False)
    s = fabrica(join_transaction_mode="create_savepoint")
    try:
        yield s
    finally:
        s.close()


class ClienteDePruebas(TestClient):
    """TestClient que, despues de cada peticion, expira los objetos que el
    test tenia cargados.

    Sin esto, un objeto leido antes de la peticion devuelve el valor viejo
    aunque la API lo haya cambiado. Lo peligroso es la direccion contraria a
    la que uno espera: un test que afirma que un contador NO cambio pasaria
    igual aunque la API lo hubiera incrementado.
    """

    def __init__(self, app_de_prueba: object, sesion: Session) -> None:
        super().__init__(app_de_prueba)  # type: ignore[arg-type]
        self._sesion = sesion

    def request(self, *args: object, **kwargs: object) -> Response:
        respuesta = super().request(*args, **kwargs)  # type: ignore[arg-type]
        self._sesion.expire_all()
        return respuesta


@pytest.fixture
def cliente(conexion: Connection, sesion: Session) -> Iterator[TestClient]:
    """Cliente de la API, con su PROPIA sesion, distinta de la del test.

    Las dos sesiones comparten la conexion y la transaccion externa, asi que
    la API ve lo que el test preparo con `sesion`. Pero la de la API se abre
    y se cierra en cada peticion, igual que `obtener_sesion` en produccion:
    si el codigo no hizo commit, su escritura se revierte y el test no la ve.

    **Por que no una sola sesion compartida.** Es lo que habia antes, y hacia
    indistinguible un servicio que commitea de uno que no: el test veia el
    cambio igual, porque era la misma sesion. Comprobado: con sesion
    compartida, un endpoint que incrementa un contador y lanza un 401 sin
    commitear dejaba el test en verde; en produccion el incremento se perdia
    y el bloqueo por intentos no se activaba nunca. Con sesion propia, ese
    test falla, que es lo que tiene que pasar.

    Por eso "el contador en la base es 3" solo es comprobable asi.
    """
    fabrica = sessionmaker(
        bind=conexion,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    def sesion_de_la_api() -> Iterator[Session]:
        s = fabrica()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = sesion_de_la_api
    try:
        with ClienteDePruebas(app, sesion) as c:
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
