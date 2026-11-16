"""Capability `grupos`: edad que cubre cada grupo (change menu-lateral-y-edad-de-grupos).

Un test por Scenario del Requirement NUEVO «Edad que cubre el grupo» de
`openspec/changes/menu-lateral-y-edad-de-grupos/specs/grupos/spec.md`
(6 Scenarios). El Requirement MODIFICADO «Grupos donde se puede inscribir»
se prueba en `test_listar_grupos.py`.

La regla: `edad_desde` = año de referencia - año de `nacimiento_hasta`;
`edad_hasta` = año de referencia - año de `nacimiento_desde`. El año de
referencia es el primer año del nombre de la temporada vigente, no su fecha
de inicio ni la fecha de hoy.

Se prueba por la API. El estado se prepara con la sesion del test, igual que
`test_listar_grupos.py`: las temporadas con el ORM y los grupos y
asignaciones con SQL crudo. Los tokens salen del login real.
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
URL_GRUPOS = "/api/v1/grupos"
CONTRASENA = "Verano2026"


# --- preparacion -----------------------------------------------------------


def _crear_temporada(
    sesion: Session,
    nombre: str,
    *,
    inicio: date = date(2026, 12, 14),
    cierre: date = date(2027, 2, 28),
) -> int:
    temporada = Temporada(
        nombre=nombre,
        fecha_inicio=inicio,
        fecha_cierre=cierre,
        estado=EstadoTemporada.VIGENTE,
    )
    sesion.add(temporada)
    sesion.flush()
    return temporada.id


def _crear_usuario(sesion: Session, username: str, rol: RolUsuario) -> int:
    usuario = Usuario(
        username=username,
        password_hash=hashear(CONTRASENA),
        debe_cambiar_password=False,
        intentos_fallidos=0,
        nombre="Juan",
        apellido="Perez",
        rol=rol,
        activo=True,
    )
    sesion.add(usuario)
    sesion.flush()
    return usuario.id


def _insertar_grupo(
    sesion: Session,
    temporada_id: int,
    nombre: str,
    turno: str,
    desde: date,
    hasta: date,
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, :n, :tu, :d, :h, true) RETURNING id"
            ),
            {"t": temporada_id, "n": nombre, "tu": turno, "d": desde, "h": hasta},
        ).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _listar(cliente: TestClient, encabezados: dict[str, str]) -> list[dict[str, Any]]:
    respuesta = cliente.get(URL_GRUPOS, headers=encabezados)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert isinstance(cuerpo, list)
    return cuerpo


def _el_grupo(grupos: list[dict[str, Any]], grupo_id: int) -> dict[str, Any]:
    encontrados = [g for g in grupos if g["id"] == grupo_id]
    assert len(encontrados) == 1, f"el grupo {grupo_id} no esta en la respuesta: {grupos}"
    return encontrados[0]


def _edades(grupo: dict[str, Any]) -> tuple[Any, Any]:
    """Las dos edades, comprobando que son enteros y no textos ni decimales."""
    desde, hasta = grupo["edad_desde"], grupo["edad_hasta"]
    assert type(desde) is int, f"edad_desde no es entero: {desde!r}"
    assert type(hasta) is int, f"edad_hasta no es entero: {hasta!r}"
    return desde, hasta


@pytest.fixture
def vigente(sesion: Session) -> int:
    return _crear_temporada(sesion, "2026-27")


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


# --- Requirement: Edad que cubre el grupo -----------------------------------


class TestEdadQueCubreElGrupo:
    def test_delfines_cubre_de_5_a_6_y_tiburones_de_7_a_9(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupos de la semilla
        delfines = _insertar_grupo(
            sesion, vigente, "Delfines", "manana", date(2020, 1, 1), date(2021, 12, 31)
        )
        tiburones = _insertar_grupo(
            sesion, vigente, "Tiburones", "manana", date(2017, 1, 1), date(2019, 12, 31)
        )

        grupos = _listar(cliente, coordinador)

        assert _edades(_el_grupo(grupos, delfines)) == (5, 6)
        assert _edades(_el_grupo(grupos, tiburones)) == (7, 9)

    def test_un_dia_de_mas_en_el_anio_siguiente_baja_la_edad_desde_a_4(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Un día de más en el año siguiente suma una edad
        pulpos = _insertar_grupo(
            sesion, vigente, "Pulpos", "manana", date(2020, 1, 1), date(2022, 1, 1)
        )

        grupos = _listar(cliente, coordinador)

        assert _edades(_el_grupo(grupos, pulpos)) == (4, 6)

    def test_un_dia_de_menos_en_el_anio_anterior_sube_la_edad_hasta_a_7(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Un día de menos en el año anterior suma una edad
        pulpos = _insertar_grupo(
            sesion, vigente, "Pulpos", "manana", date(2019, 12, 31), date(2021, 12, 31)
        )

        grupos = _listar(cliente, coordinador)

        assert _edades(_el_grupo(grupos, pulpos)) == (5, 7)

    def test_un_grupo_de_un_solo_anio_trae_la_misma_edad_en_los_dos_extremos(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Grupo de un solo año
        pulpos = _insertar_grupo(
            sesion, vigente, "Pulpos", "manana", date(2019, 1, 1), date(2019, 12, 31)
        )

        grupos = _listar(cliente, coordinador)

        assert _edades(_el_grupo(grupos, pulpos)) == (7, 7)

    def test_la_edad_se_cuenta_desde_el_anio_del_nombre_y_no_desde_la_fecha_de_inicio(
        self,
        cliente: TestClient,
        sesion: Session,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: La referencia es el nombre de la temporada, no su fecha de inicio
        # Unica temporada vigente: «2027-28», que empieza el 2028-01-03. Si la
        # referencia fuera el año de inicio, daria 7 y 8.
        temporada = _crear_temporada(
            sesion, "2027-28", inicio=date(2028, 1, 3), cierre=date(2028, 2, 28)
        )
        delfines = _insertar_grupo(
            sesion, temporada, "Delfines", "manana", date(2020, 1, 1), date(2021, 12, 31)
        )

        grupos = _listar(cliente, coordinador)

        assert _edades(_el_grupo(grupos, delfines)) == (6, 7)

    def test_el_profesor_recibe_solo_delfines_manana_con_edad_de_5_a_6(
        self, cliente: TestClient, sesion: Session, vigente: int
    ) -> None:
        # Scenario: El Profesor recibe la edad solo de sus grupos
        delfines = _insertar_grupo(
            sesion, vigente, "Delfines", "manana", date(2020, 1, 1), date(2021, 12, 31)
        )
        # Otro grupo de la temporada, asignado a otro profesor: no tiene que venir.
        tiburones = _insertar_grupo(
            sesion, vigente, "Tiburones", "manana", date(2017, 1, 1), date(2019, 12, 31)
        )
        jperez = _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        _asignar(sesion, delfines, jperez)
        otro = _crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        _asignar(sesion, tiburones, otro)

        grupos = _listar(cliente, _ingresar(cliente, "jperez"))

        assert len(grupos) == 1
        unico = grupos[0]
        assert unico["id"] == delfines
        assert (unico["nombre"], unico["turno"]) == ("Delfines", "manana")
        assert _edades(unico) == (5, 6)
