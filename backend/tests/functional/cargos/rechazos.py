"""Ayudas para los tests de rechazos del registro de cargos (tarea 3.2).

No es un archivo de tests (pytest no lo junta: no empieza con `test_`). Lo
usan `test_rechazos_forma.py`, `test_rechazos_temporada.py`,
`test_rechazos_configuracion.py` y `test_repetidos.py`.

La forma de un rechazo de regla del negocio sale de la spec
`errores-de-la-api`, «Rechazos de reglas del negocio con la forma de
validación»: 422, `detail` lista, `loc` terminado en el campo, `msg` y
`type` `regla_de_negocio`.
"""

from typing import Any

from sqlalchemy.orm import Session

from tests.functional.cargos.preparacion import (
    errores_con_loc_terminado_en,
    tarifa,
    todos_los_descuentos,
)

# Ids que no existen en ninguna tabla de una base de pruebas (caben en int4).
ID_INEXISTENTE = 2_000_000_000

MODALIDADES = ("mes", "quincena", "semana", "dia")


def tarifario_completo(sesion: Session, temporada_id: int, categoria: str) -> None:
    """Tarifa base en los dos turnos y las cuatro modalidades, y todos los
    descuentos de la categoria: que un rechazo no salga de un tarifario
    incompleto sino de la regla que se prueba."""
    for turno in ("manana", "tarde"):
        for modalidad in MODALIDADES:
            tarifa(sesion, temporada_id, turno, modalidad, "100000.00")
    todos_los_descuentos(sesion, temporada_id, categoria, "10.00")


def campo_del_error(error: dict[str, Any]) -> Any:
    return list(error["loc"])[-1]


def exigir_rechazo(respuesta: Any, esperados: dict[str, str]) -> None:
    """Exige un 422 con un error `regla_de_negocio` por cada campo esperado,
    con su `msg` exacto, todos en la misma respuesta, y ningun error en otro
    campo: el resto del pedido es valido, asi que otro error seria ruido de
    la preparacion o una regla que la spec no pide."""
    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    assert {campo_del_error(e) for e in detalle} == set(esperados), detalle
    for campo, mensaje in esperados.items():
        errores = errores_con_loc_terminado_en(respuesta, campo)
        assert [e["msg"] for e in errores] == [mensaje], detalle
        assert all(e["type"] == "regla_de_negocio" for e in errores), detalle
