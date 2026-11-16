"""El unico test que no viene de una historia.

Comprueba que el andamiaje funciona: que la aplicacion arranca, que la base
de pruebas esta migrada y que el aislamiento por transaccion esta puesto.
Si este test falla, ningun otro significa nada.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_la_aplicacion_responde(cliente: TestClient) -> None:
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_el_contrato_de_la_api_se_puede_generar(cliente: TestClient) -> None:
    respuesta = cliente.get("/openapi.json")
    assert respuesta.status_code == 200
    assert respuesta.json()["info"]["title"] == "Escuelita de Verano"


def test_la_base_de_pruebas_es_postgres(sesion: Session) -> None:
    from sqlalchemy import text

    version = sesion.execute(text("SELECT version()")).scalar_one()
    assert "PostgreSQL" in str(version), (
        "La base de los tests no es Postgres. Con otro motor, los errores de "
        "restricciones y de precision numerica no aparecen."
    )
