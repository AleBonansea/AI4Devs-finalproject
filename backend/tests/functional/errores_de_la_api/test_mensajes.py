"""Capability `errores-de-la-api`: mensajes de validacion en castellano
(change familias-y-alumnos, tarea 4.2).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/errores-de-la-api/spec.md`,
Requirement «Mensajes de validación en castellano» (8 Scenarios).

Se prueba por la API. Seis Scenarios usan `POST /api/v1/alumnos` con un
Coordinador y un cuerpo valido (igual que `alumnos/test_alta.py`) en el que
se cambia solo el campo que prueba cada uno. El ultimo usa
`POST /api/v1/auth/login`.

El error «de un campo» es el elemento de `detail` cuyo `loc` termina en ese
campo. Se compara el `msg` exacto.
"""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hashear
from app.models import EstadoTemporada, RolUsuario, Temporada, Usuario

URL_LOGIN = "/api/v1/auth/login"
URL_ALUMNOS = "/api/v1/alumnos"
URL_FAMILIAS = "/api/v1/familias"
CONTRASENA = "Verano2026"

# Marca para quitar una clave del cuerpo base.
OMITIR = object()


# --- preparacion -----------------------------------------------------------


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _cuerpo(grupo_id: int, **cambios: Any) -> dict[str, Any]:
    """Un alta valida de Juan Perez con familia nueva `empleado` y Maria Perez
    nueva como tutora. `cambios` pisa claves; `OMITIR` las quita."""
    cuerpo: dict[str, Any] = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "fecha_nacimiento": "2020-03-10",
        "grupo_id": grupo_id,
        "categoria": "empleado",
        "personas": [
            {
                "nombre": "María",
                "apellido": "Pérez",
                "telefono": "3511234567",
                "dni": "30111222",
                "es_tutor": True,
            }
        ],
    }
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not OMITIR}


def _afirmar_msg(respuesta: Any, campo: str, msg: str) -> None:
    """422, al menos un error cuyo `loc` termina en `campo`, y todos los de ese
    campo con `msg` exacto."""
    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert isinstance(detalle, list), detalle
    errores = [e for e in detalle if e["loc"] and e["loc"][-1] == campo]
    assert errores, f"no hay error en {campo}: {respuesta.text}"
    assert [e["msg"] for e in errores] == [msg] * len(errores), respuesta.text


def _claves_input(valor: Any) -> list[Any]:
    """Todas las apariciones de una clave `input`, en cualquier nivel."""
    if isinstance(valor, dict):
        encontradas = [valor["input"]] if "input" in valor else []
        for v in valor.values():
            encontradas.extend(_claves_input(v))
        return encontradas
    if isinstance(valor, list):
        encontradas = []
        for v in valor:
            encontradas.extend(_claves_input(v))
        return encontradas
    return []


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def delfines_manana(sesion: Session) -> int:
    """«Delfines» mañana de la temporada vigente."""
    temporada = Temporada(
        nombre="2026-27",
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, 'Delfines', 'manana', :d, :h, true) RETURNING id"
            ),
            {"t": temporada.id, "d": date(2020, 1, 1), "h": date(2021, 12, 31)},
        ).scalar_one()
    )


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    sesion.add(
        Usuario(
            username="coordi",
            password_hash=hashear(CONTRASENA),
            debe_cambiar_password=False,
            intentos_fallidos=0,
            nombre="Juan",
            apellido="Perez",
            rol=RolUsuario.COORDINADOR,
            activo=True,
        )
    )
    sesion.flush()
    return _ingresar(cliente, "coordi")


# --- Requirement: Mensajes de validación en castellano ---------------------


class TestMensajesDeValidacionEnCastellano:
    def test_un_dato_que_falta_dice_este_dato_es_obligatorio(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Dato que falta
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, fecha_nacimiento=OMITIR),
        )

        _afirmar_msg(respuesta, "fecha_nacimiento", "Este dato es obligatorio.")

    def test_un_texto_mas_largo_que_el_maximo_dice_puede_tener_hasta_80_caracteres(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Texto más largo que el máximo
        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, nombre="J" * 81)
        )

        _afirmar_msg(respuesta, "nombre", "Puede tener hasta 80 caracteres.")

    def test_un_texto_que_queda_vacio_dice_no_puede_quedar_vacio(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Texto que queda vacío
        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, apellido="   ")
        )

        _afirmar_msg(respuesta, "apellido", "No puede quedar vacío.")

    def test_un_texto_mas_corto_que_un_minimo_dice_tiene_que_tener_al_menos_2_caracteres(
        self, cliente: TestClient, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Texto más corto que un mínimo mayor que uno
        respuesta = cliente.get(URL_FAMILIAS, headers=coordinador, params={"apellido": " P "})

        _afirmar_msg(respuesta, "apellido", "Tiene que tener al menos 2 caracteres.")

    def test_un_numero_mal_escrito_dice_tiene_que_ser_un_numero_entero(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Número mal escrito
        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json={**_cuerpo(delfines_manana), "grupo_id": "uno"}
        )

        _afirmar_msg(respuesta, "grupo_id", "Tiene que ser un número entero.")

    def test_una_fecha_mal_escrita_dice_la_fecha_no_es_valida(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Fecha mal escrita
        respuesta = cliente.post(
            URL_ALUMNOS,
            headers=coordinador,
            json=_cuerpo(delfines_manana, fecha_nacimiento="10/03/2020"),
        )

        _afirmar_msg(respuesta, "fecha_nacimiento", "La fecha no es válida.")

    def test_una_categoria_que_no_existe_dice_el_valor_no_es_una_de_las_opciones_validas(
        self, cliente: TestClient, delfines_manana: int, coordinador: dict[str, str]
    ) -> None:
        # Scenario: Categoría que no existe
        respuesta = cliente.post(
            URL_ALUMNOS, headers=coordinador, json=_cuerpo(delfines_manana, categoria="vip")
        )

        _afirmar_msg(respuesta, "categoria", "El valor no es una de las opciones válidas.")

    def test_un_usuario_del_login_de_61_caracteres_dice_hasta_60_y_no_devuelve_input(
        self, cliente: TestClient
    ) -> None:
        # Scenario: Usuario del login demasiado largo
        respuesta = cliente.post(URL_LOGIN, json={"username": "u" * 61, "password": CONTRASENA})

        _afirmar_msg(respuesta, "username", "Puede tener hasta 60 caracteres.")
        # AND el cuerpo no tiene ningún campo `input`, en ningun nivel.
        assert _claves_input(respuesta.json()) == [], respuesta.text
