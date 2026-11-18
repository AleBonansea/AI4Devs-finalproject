"""Capability `semilla`: el permiso explicito para sembrar una base remota.

Un test por Scenario nuevo o modificado de
`openspec/changes/semilla-fuera-de-local/specs/semilla/spec.md`.

La interfaz la fija `design.md` («Una función nueva, `comprobar_destino(url,
entorno)`»): devuelve `None` si la URL es local, el texto del aviso si es
remota y el entorno trae `SEMILLA_FUERA_DE_LOCAL` igual a `1`, y si no deja
pasar `SemillaRechazada`. El entorno llega como `dict`, asi que el permiso se
prueba sin tocar el entorno real del proceso de tests.

«El aviso sale antes de conectarse» corre `python tasks.py seed` en un
proceso aparte, desde la raiz del repo, como dice el Scenario, contra un host
`.invalid`, que es un dominio reservado y nunca resuelve.

Los Scenarios de base local tambien se prueban contra `comprobar_destino` sin
permiso (design.md, «Cómo se prueba»): es lo unico que llama el script, y
probarlos solo contra `verificar_base_local` deja en verde a un
`comprobar_destino` que rechace todo.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RolUsuario, Usuario
from app.semilla import SemillaRechazada, cargar, comprobar_destino

MENSAJE_BASE_NO_LOCAL = "La semilla solo corre contra una base local."
MENSAJE_BASE_NO_VACIA = "La base no está vacía: la semilla solo corre sobre una base vacía."
MENSAJE_HOST_VACIO = (
    "La semilla no siembra una base remota sin nombrar su host: la URL tiene un host vacío."
)
PERMISO = {"SEMILLA_FUERA_DE_LOCAL": "1"}

URL_REMOTA = "postgresql+psycopg://u:p@dpg-abc123.oregon-postgres.render.com/escuelita"
URL_LOCAL = "postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita"
URL_HOST_EN_QUERY = (
    "postgresql+psycopg://u:p@localhost/escuelita?host=dpg-abc123.oregon-postgres.render.com"
)
AVISO_RENDER = (
    "Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: "
    "dpg-abc123.oregon-postgres.render.com."
)

CARPETA_BACKEND = Path(__file__).resolve().parents[3]
RAIZ = CARPETA_BACKEND.parent


# --- Requirement: La semilla solo corre contra una base local (modificado) ---


def test_sin_la_variable_la_base_del_docker_compose_puede_correr() -> None:
    url = "postgresql+psycopg://escuelita:escuelita@db:5432/escuelita"
    assert comprobar_destino(url, {}) is None


def test_sin_la_variable_la_base_en_localhost_puede_correr() -> None:
    assert comprobar_destino(URL_LOCAL, {}) is None


def test_sin_la_variable_un_host_local_con_puerto_en_la_query_puede_correr() -> None:
    url = "postgresql+psycopg://u:p@localhost/escuelita?host=localhost:5432"
    assert comprobar_destino(url, {}) is None


def test_sin_la_variable_una_base_remota_se_rechaza_por_no_ser_local() -> None:
    with pytest.raises(SemillaRechazada) as error:
        comprobar_destino(URL_REMOTA, {})
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


# --- Requirement: Permiso explícito para sembrar una base remota -------------


def test_con_el_permiso_una_base_remota_se_acepta_y_avisa_con_su_host() -> None:
    aviso = comprobar_destino(URL_REMOTA, {"SEMILLA_FUERA_DE_LOCAL": "1"})
    assert aviso == AVISO_RENDER


def test_con_el_permiso_el_aviso_nombra_el_host_escondido_en_la_query() -> None:
    aviso = comprobar_destino(URL_HOST_EN_QUERY, {"SEMILLA_FUERA_DE_LOCAL": "1"})
    assert aviso == AVISO_RENDER


def test_con_el_permiso_el_aviso_nombra_cada_host_remoto_una_sola_vez() -> None:
    url = (
        "postgresql+psycopg://u:p@dpg-a.oregon-postgres.render.com/escuelita"
        "?host=dpg-b.oregon-postgres.render.com,dpg-a.oregon-postgres.render.com"
    )
    aviso = comprobar_destino(url, PERMISO)
    assert aviso == (
        "Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: "
        "dpg-a.oregon-postgres.render.com, dpg-b.oregon-postgres.render.com."
    )


def test_con_el_permiso_el_aviso_nombra_el_host_sin_su_puerto() -> None:
    url = (
        "postgresql+psycopg://u:p@localhost/escuelita"
        "?host=dpg-abc123.oregon-postgres.render.com:5432"
    )
    assert comprobar_destino(url, PERMISO) == AVISO_RENDER


def test_con_el_permiso_una_base_local_se_acepta_sin_aviso() -> None:
    assert comprobar_destino(URL_LOCAL, {"SEMILLA_FUERA_DE_LOCAL": "1"}) is None


def test_la_variable_en_cero_no_da_el_permiso() -> None:
    with pytest.raises(SemillaRechazada) as error:
        comprobar_destino(URL_REMOTA, {"SEMILLA_FUERA_DE_LOCAL": "0"})
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


def test_la_variable_en_true_no_da_el_permiso() -> None:
    with pytest.raises(SemillaRechazada) as error:
        comprobar_destino(URL_REMOTA, {"SEMILLA_FUERA_DE_LOCAL": "true"})
    assert str(error.value) == MENSAJE_BASE_NO_LOCAL


def test_el_aviso_sale_antes_del_error_de_conexion_y_el_comando_termina_con_error() -> None:
    entorno = dict(os.environ)
    entorno["SEMILLA_FUERA_DE_LOCAL"] = "1"
    entorno["DATABASE_URL"] = "postgresql+psycopg://u:p@dpg-noexiste.invalid/escuelita"
    # Para leer el acento del aviso sin depender de la pagina de codigos de
    # la consola de Windows.
    entorno["PYTHONIOENCODING"] = "utf-8"

    # `tasks.py` escribe en stdout la linea `$ <comando>` antes de lanzar el
    # script; el aviso y el error de conexion van por stderr.
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "tasks.py"), "seed"],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        timeout=120,
    )
    stderr = resultado.stderr.decode("utf-8", errors="replace")

    aviso = (
        "Atención: SEMILLA_FUERA_DE_LOCAL=1. La semilla va a escribir en una base remota: "
        "dpg-noexiste.invalid."
    )
    assert resultado.returncode != 0, stderr
    assert aviso in stderr, stderr

    # Ningun rastro del error de conexion puede aparecer antes del aviso.
    indice_aviso = stderr.index(aviso)
    rastros = ("Traceback", "OperationalError", "psycopg", "could not translate", "failed")
    for rastro in rastros:
        indice = stderr.find(rastro)
        if indice != -1:
            assert indice_aviso < indice, (rastro, stderr)


# --- Requirement: Con el permiso, un host vacío se rechaza ------------------


def test_con_el_permiso_una_url_sin_host_se_rechaza_por_host_vacio() -> None:
    with pytest.raises(SemillaRechazada) as error:
        comprobar_destino("postgresql+psycopg://u:p@/escuelita", PERMISO)
    assert str(error.value) == MENSAJE_HOST_VACIO


def test_con_el_permiso_un_elemento_vacio_en_la_lista_de_hosts_se_rechaza() -> None:
    with pytest.raises(SemillaRechazada) as error:
        comprobar_destino("postgresql+psycopg://u:p@localhost/escuelita?host=localhost,", PERMISO)
    assert str(error.value) == MENSAJE_HOST_VACIO


# --- Requirement: Permiso explícito (base no vacía) ---------------------------


def test_con_el_permiso_la_base_no_vacia_se_sigue_rechazando_sin_escribir_nada(
    sesion: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEMILLA_FUERA_DE_LOCAL", "1")
    sesion.add(
        Usuario(
            username="aperez",
            password_hash="$argon2id$no-es-un-hash-real",
            nombre="Ana",
            apellido="Perez",
            rol=RolUsuario.ADMIN,
        )
    )
    sesion.flush()

    with pytest.raises(SemillaRechazada) as error:
        cargar(sesion)

    assert str(error.value) == MENSAJE_BASE_NO_VACIA
    sesion.flush()
    assert sesion.execute(text("SELECT username FROM usuario")).scalars().all() == ["aperez"]
    for tabla in (
        "temporada",
        "grupo",
        "grupo_profesor",
        "tarifa_base",
        "descuento_modalidad",
        "descuento_mes",
        "periodo_cobro",
        "tipo_cargo",
    ):
        assert sesion.execute(text(f"SELECT count(*) FROM {tabla}")).scalar_one() == 0, tabla
