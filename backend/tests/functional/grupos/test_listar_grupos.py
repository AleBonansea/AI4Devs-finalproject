"""Capability `grupos`: `GET /api/v1/grupos` (change familias-y-alumnos, tarea 2.1).

Un test por Scenario de
`openspec/changes/familias-y-alumnos/specs/grupos/spec.md`:
- Requirement «Grupos donde se puede inscribir» (5 Scenarios).
- Requirement «Grupo sugerido por fecha de nacimiento» (6 Scenarios).

Se prueba por la API. El estado se prepara con la sesion del test: las
temporadas con el ORM y los grupos y asignaciones con SQL crudo sobre los
nombres del modelo de datos, igual que `test_grupos.py`. Los tokens salen
del login real.
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

CAMPOS_DEL_GRUPO = {"id", "nombre", "turno", "nacimiento_desde", "nacimiento_hasta", "sugerido"}

DESDE = date(2020, 1, 1)
HASTA = date(2021, 12, 31)


# --- preparacion -----------------------------------------------------------


def _crear_temporada(sesion: Session, nombre: str, estado: EstadoTemporada) -> int:
    temporada = Temporada(
        nombre=nombre,
        fecha_inicio=date(2026, 12, 14),
        fecha_cierre=date(2027, 2, 28),
        estado=estado,
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
    *,
    desde: date = DESDE,
    hasta: date = HASTA,
    activo: bool = True,
) -> int:
    return int(
        sesion.execute(
            text(
                "INSERT INTO grupo (temporada_id, nombre, turno, nacimiento_desde, "
                "nacimiento_hasta, activo) "
                "VALUES (:t, :n, :tu, :d, :h, :a) RETURNING id"
            ),
            {"t": temporada_id, "n": nombre, "tu": turno, "d": desde, "h": hasta, "a": activo},
        ).scalar_one()
    )


def _asignar(sesion: Session, grupo_id: int, usuario_id: int) -> None:
    sesion.execute(
        text("INSERT INTO grupo_profesor (grupo_id, usuario_id) VALUES (:g, :u)"),
        {"g": grupo_id, "u": usuario_id},
    )


def _cuatro_grupos(sesion: Session, temporada_id: int) -> dict[tuple[str, str], int]:
    """«Delfines» y «Tiburones» activos de cada turno. Se insertan en un orden
    distinto del esperado, para que el orden de la respuesta no salga gratis
    del orden de insercion."""
    ids: dict[tuple[str, str], int] = {}
    for nombre, turno in (
        ("Tiburones", "tarde"),
        ("Tiburones", "manana"),
        ("Delfines", "tarde"),
        ("Delfines", "manana"),
    ):
        ids[(nombre, turno)] = _insertar_grupo(sesion, temporada_id, nombre, turno)
    return ids


def _ingresar(cliente: TestClient, username: str) -> dict[str, str]:
    respuesta = cliente.post(URL_LOGIN, json={"username": username, "password": CONTRASENA})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def _listar(
    cliente: TestClient, encabezados: dict[str, str], fecha: str | None = None
) -> list[dict[str, Any]]:
    params = {"fecha_nacimiento": fecha} if fecha is not None else None
    respuesta = cliente.get(URL_GRUPOS, headers=encabezados, params=params)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert isinstance(cuerpo, list)
    return cuerpo


def _el_grupo(grupos: list[dict[str, Any]], grupo_id: int) -> dict[str, Any]:
    encontrados = [g for g in grupos if g["id"] == grupo_id]
    assert len(encontrados) == 1, f"el grupo {grupo_id} no esta en la respuesta: {grupos}"
    return encontrados[0]


@pytest.fixture
def vigente(sesion: Session) -> int:
    return _crear_temporada(sesion, "2026-27", EstadoTemporada.VIGENTE)


@pytest.fixture
def coordinador(cliente: TestClient, sesion: Session) -> dict[str, str]:
    _crear_usuario(sesion, "coordi", RolUsuario.COORDINADOR)
    return _ingresar(cliente, "coordi")


@pytest.fixture
def delfines_manana(sesion: Session, vigente: int) -> int:
    """«Delfines» mañana, para nacidos del 2020-01-01 al 2021-12-31."""
    return _insertar_grupo(sesion, vigente, "Delfines", "manana")


# --- Requirement: Grupos donde se puede inscribir --------------------------


class TestGruposDondeSePuedeInscribir:
    def test_el_coordinador_recibe_los_grupos_activos_por_turno_y_nombre_sin_los_inactivos(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Coordinador ve todos los grupos activos
        ids = _cuatro_grupos(sesion, vigente)
        pulpos = _insertar_grupo(sesion, vigente, "Pulpos", "manana", activo=False)

        grupos = _listar(cliente, coordinador)

        assert [(g["nombre"], g["turno"]) for g in grupos] == [
            ("Delfines", "manana"),
            ("Tiburones", "manana"),
            ("Delfines", "tarde"),
            ("Tiburones", "tarde"),
        ]
        assert [g["id"] for g in grupos] == [
            ids[("Delfines", "manana")],
            ids[("Tiburones", "manana")],
            ids[("Delfines", "tarde")],
            ids[("Tiburones", "tarde")],
        ]
        # AND no incluye «Pulpos»
        assert pulpos not in [g["id"] for g in grupos]
        assert "Pulpos" not in [g["nombre"] for g in grupos]
        # Cada grupo trae exactamente los campos del contrato.
        for g in grupos:
            assert set(g) == CAMPOS_DEL_GRUPO
        delfines = grupos[0]
        assert delfines["nacimiento_desde"] == "2020-01-01"
        assert delfines["nacimiento_hasta"] == "2021-12-31"

    def test_el_admin_no_recibe_los_grupos_de_la_temporada_cerrada(
        self, cliente: TestClient, sesion: Session, vigente: int
    ) -> None:
        # Scenario: Grupos de otra temporada
        cerrada = _crear_temporada(sesion, "2025-26", EstadoTemporada.CERRADA)
        delfines_cerrada = _insertar_grupo(sesion, cerrada, "Delfines", "manana")
        # Contraste: el mismo grupo en la vigente si tiene que venir.
        delfines_vigente = _insertar_grupo(sesion, vigente, "Delfines", "manana")
        _crear_usuario(sesion, "admin1", RolUsuario.ADMIN)

        grupos = _listar(cliente, _ingresar(cliente, "admin1"))

        ids = [g["id"] for g in grupos]
        assert delfines_cerrada not in ids
        assert ids == [delfines_vigente]

    def test_el_profesor_recibe_un_solo_grupo_el_que_tiene_asignado(
        self, cliente: TestClient, sesion: Session, vigente: int
    ) -> None:
        # Scenario: Profesor ve solo sus grupos
        ids = _cuatro_grupos(sesion, vigente)
        jperez = _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)
        _asignar(sesion, ids[("Delfines", "manana")], jperez)
        # Otro profesor con los demas grupos: el filtro tiene que ser por el
        # profesor del token, no por "grupos con algun profesor".
        otro = _crear_usuario(sesion, "cfernandez", RolUsuario.PROFESOR)
        for clave in (("Tiburones", "manana"), ("Delfines", "tarde"), ("Tiburones", "tarde")):
            _asignar(sesion, ids[clave], otro)

        grupos = _listar(cliente, _ingresar(cliente, "jperez"))

        assert len(grupos) == 1
        assert grupos[0]["id"] == ids[("Delfines", "manana")]
        assert (grupos[0]["nombre"], grupos[0]["turno"]) == ("Delfines", "manana")

    def test_el_profesor_sin_grupos_recibe_una_lista_vacia(
        self, cliente: TestClient, sesion: Session, vigente: int
    ) -> None:
        # Scenario: Profesor sin grupos
        # Hay grupos activos en la vigente: la lista vacia no sale de que no
        # exista ninguno.
        _cuatro_grupos(sesion, vigente)
        _crear_usuario(sesion, "jperez", RolUsuario.PROFESOR)

        respuesta = cliente.get(URL_GRUPOS, headers=_ingresar(cliente, "jperez"))

        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json() == []

    def test_sin_token_responde_401(
        self, cliente: TestClient, sesion: Session, vigente: int
    ) -> None:
        # Scenario: Sin sesión
        _cuatro_grupos(sesion, vigente)

        respuesta = cliente.get(URL_GRUPOS)

        assert respuesta.status_code == 401, respuesta.text


# --- Requirement: Grupo sugerido por fecha de nacimiento -------------------


class TestGrupoSugerido:
    def test_el_primer_dia_del_rango_marca_el_grupo_como_sugerido(
        self, cliente: TestClient, coordinador: dict[str, str], delfines_manana: int
    ) -> None:
        # Scenario: Primer día del rango
        grupos = _listar(cliente, coordinador, "2020-01-01")

        assert _el_grupo(grupos, delfines_manana)["sugerido"] is True

    def test_el_dia_anterior_al_rango_no_lo_sugiere_pero_el_grupo_sigue_en_la_respuesta(
        self, cliente: TestClient, coordinador: dict[str, str], delfines_manana: int
    ) -> None:
        # Scenario: Día anterior al rango
        grupos = _listar(cliente, coordinador, "2019-12-31")

        # AND la respuesta sigue incluyendo a «Delfines» mañana (_el_grupo
        # falla si no esta).
        assert _el_grupo(grupos, delfines_manana)["sugerido"] is False

    def test_el_ultimo_dia_del_rango_marca_el_grupo_como_sugerido(
        self, cliente: TestClient, coordinador: dict[str, str], delfines_manana: int
    ) -> None:
        # Scenario: Último día del rango
        grupos = _listar(cliente, coordinador, "2021-12-31")

        assert _el_grupo(grupos, delfines_manana)["sugerido"] is True

    def test_el_dia_posterior_al_rango_no_lo_sugiere(
        self, cliente: TestClient, coordinador: dict[str, str], delfines_manana: int
    ) -> None:
        # Scenario: Día posterior al rango
        grupos = _listar(cliente, coordinador, "2022-01-01")

        assert _el_grupo(grupos, delfines_manana)["sugerido"] is False

    def test_el_mismo_rango_en_los_dos_turnos_sugiere_los_dos_grupos(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
        delfines_manana: int,
    ) -> None:
        # Scenario: Sugerido en los dos turnos
        delfines_tarde = _insertar_grupo(sesion, vigente, "Delfines", "tarde")

        grupos = _listar(cliente, coordinador, "2020-03-10")

        assert _el_grupo(grupos, delfines_manana)["sugerido"] is True
        assert _el_grupo(grupos, delfines_tarde)["sugerido"] is True

    def test_sin_fecha_ningun_grupo_viene_sugerido(
        self,
        cliente: TestClient,
        sesion: Session,
        vigente: int,
        coordinador: dict[str, str],
    ) -> None:
        # Scenario: Sin fecha
        ids = _cuatro_grupos(sesion, vigente)

        grupos = _listar(cliente, coordinador)

        assert sorted(g["id"] for g in grupos) == sorted(ids.values())
        assert [g["sugerido"] for g in grupos] == [False] * 4
