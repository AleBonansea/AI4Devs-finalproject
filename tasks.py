#!/usr/bin/env python3
"""Las tareas del proyecto. Una sola fuente para Windows, Linux y el CI.

    python tasks.py            lista las tareas
    python tasks.py test       corre los tests del backend

Antes esto era un Makefile, y `make` no viene con Windows: todo lo que
CLAUDE.md, las skills y el CI documentaban no se podia correr en la maquina
donde se programa. Un comando documentado que no existe es una regla que no
se cumple.

No tiene dependencias propias: se arranca con el Python del sistema y el
resto sale del entorno virtual de backend/.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BACKEND = RAIZ / "backend"
FRONTEND = RAIZ / "frontend"
VENV = BACKEND / ".venv"
ES_WINDOWS = platform.system() == "Windows"
BIN = VENV / ("Scripts" if ES_WINDOWS else "bin")
NPM = "npm.cmd" if ES_WINDOWS else "npm"


def ejecutable(nombre: str) -> str:
    """El ejecutable, del entorno virtual o del PATH.

    Primero mira `backend/.venv`, que es como se trabaja en local. Si no
    esta, cae al PATH: en el CI las dependencias se instalan en el Python
    del runner y no hay entorno virtual, y sin esta caida el CI fallaria
    siempre buscando una carpeta que nunca existio.
    """
    for sufijo in ((".exe", ".cmd", "") if ES_WINDOWS else ("",)):
        ruta = BIN / (nombre + sufijo)
        if ruta.is_file():
            return str(ruta)
    del_path = shutil.which(nombre)
    if del_path:
        return del_path
    sys.exit(
        f"No encontre '{nombre}' ni en {BIN} ni en el PATH.\n"
        f"Falta el entorno virtual o las dependencias:\n"
        f"    python tasks.py install"
    )


def correr(partes: list[str], cwd: Path = RAIZ, permitir_fallo: bool = False) -> int:
    """Corre un comando y corta con su mismo codigo de salida.

    Propagar el codigo no es un detalle: es lo que hace que el CI falle
    cuando algo falla. Un lanzador que siempre devuelve 0 apaga el CI
    entero sin que nadie lo note.
    """
    print(f"$ {' '.join(partes)}", flush=True)
    # El bin del entorno virtual al frente del PATH: no alcanza con llamar
    # al ejecutable por ruta absoluta, porque los hijos de ese proceso
    # (pytest llamando a alembic, por ejemplo) buscan en el PATH.
    entorno = dict(os.environ)
    if BIN.is_dir():
        entorno["PATH"] = str(BIN) + os.pathsep + entorno.get("PATH", "")
    codigo = subprocess.run(partes, cwd=cwd, env=entorno).returncode
    if codigo != 0 and not permitir_fallo:
        sys.exit(codigo)
    return codigo


def install() -> None:
    """Instala las dependencias de backend y frontend."""
    if not VENV.is_dir():
        correr([sys.executable, "-m", "venv", str(VENV)])
    correr([ejecutable("pip"), "install", "-e", ".[dev]"], cwd=BACKEND)
    if (FRONTEND / "package.json").is_file():
        correr([NPM, "ci"], cwd=FRONTEND)


def up() -> None:
    """Levanta Postgres en Docker y crea la base de pruebas."""
    correr(["docker", "compose", "up", "-d", "db"])
    # Si la base de pruebas ya existe, createdb falla y esta bien.
    correr(
        ["docker", "compose", "exec", "-T", "db", "createdb", "-U", "escuelita", "escuelita_test"],
        permitir_fallo=True,
    )


def down() -> None:
    """Baja Postgres. Sin -v: el volumen con los datos se conserva."""
    correr(["docker", "compose", "down"])


def api() -> None:
    """Levanta la API en desarrollo, con recarga."""
    correr([ejecutable("uvicorn"), "app.main:app", "--reload"], cwd=BACKEND)


def migrate() -> None:
    """Aplica las migraciones pendientes."""
    correr([ejecutable("alembic"), "upgrade", "head"], cwd=BACKEND)


def seed() -> None:
    """Carga datos de ejemplo. Nunca datos reales."""
    correr([ejecutable("python"), str(RAIZ / "scripts" / "seed.py")], cwd=BACKEND)


def test() -> None:
    """Tests del backend."""
    correr([ejecutable("pytest"), "-q"], cwd=BACKEND)


def lint() -> None:
    """ruff check + ruff format --check."""
    ruff = ejecutable("ruff")
    correr([ruff, "check", "."], cwd=BACKEND)
    correr([ruff, "format", "--check", "."], cwd=BACKEND)


def formato() -> None:
    """Formatea el backend."""
    ruff = ejecutable("ruff")
    correr([ruff, "format", "."], cwd=BACKEND)
    correr([ruff, "check", "--fix", "."], cwd=BACKEND)


def typecheck() -> None:
    """mypy sobre app/."""
    correr([ejecutable("mypy"), "app"], cwd=BACKEND)


_GUION_OPENAPI = """
import json, pathlib, sys
sys.path.insert(0, ".")
from app.main import app
destino = pathlib.Path(sys.argv[1])
destino.parent.mkdir(parents=True, exist_ok=True)
# newline="\\n" a proposito: sin eso, en Windows Python traduce cada \\n a
# \\r\\n y el contrato generado alla no coincide byte a byte con el generado
# en el CI. Hoy no se nota porque git normaliza al commitear, pero eso
# depende de core.autocrlf: con otra configuracion, openapi-check falla
# siempre. Generar igual en las tres plataformas no depende de nadie.
destino.write_text(
    json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\\n",
    encoding="utf-8",
    newline="\\n",
)
print("escrito", destino)
"""


def openapi_generate() -> None:
    """Regenera docs/api/openapi.json desde la aplicacion."""
    destino = RAIZ / "docs" / "api" / "openapi.json"
    correr([ejecutable("python"), "-c", _GUION_OPENAPI, str(destino)], cwd=BACKEND)


def openapi_check() -> None:
    """Falla si el contrato no esta al dia con el codigo."""
    openapi_generate()
    correr(["git", "diff", "--exit-code", "--", "docs/api/openapi.json"])


def front_lint() -> None:
    """eslint, prettier y build del frontend."""
    correr([NPM, "run", "lint"], cwd=FRONTEND)
    correr([NPM, "run", "build"], cwd=FRONTEND)


def front_dev() -> None:
    """Frontend en desarrollo."""
    correr([NPM, "run", "dev"], cwd=FRONTEND)


TAREAS = {
    "install": install,
    "up": up,
    "down": down,
    "api": api,
    "migrate": migrate,
    "seed": seed,
    "test": test,
    "lint": lint,
    "formato": formato,
    "typecheck": typecheck,
    "openapi-generate": openapi_generate,
    "openapi-check": openapi_check,
    "front-lint": front_lint,
    "front-dev": front_dev,
}


def ayuda() -> None:
    print("Tareas del proyecto. Uso: python tasks.py <tarea>\n")
    for nombre, funcion in TAREAS.items():
        doc = (funcion.__doc__ or "").strip().splitlines()[0]
        print(f"  {nombre:<18} {doc}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        ayuda()
        return
    nombre = sys.argv[1]
    if nombre not in TAREAS:
        print(f"No existe la tarea '{nombre}'.\n", file=sys.stderr)
        ayuda()
        sys.exit(2)
    TAREAS[nombre]()


if __name__ == "__main__":
    main()
