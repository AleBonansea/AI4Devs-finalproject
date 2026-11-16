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
    for sufijo in (".exe", ".cmd", "") if ES_WINDOWS else ("",):
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


def correr(
    partes: list[str],
    cwd: Path = RAIZ,
    permitir_fallo: bool = False,
    entorno_extra: dict[str, str] | None = None,
) -> int:
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
    entorno.update(entorno_extra or {})
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
    if (RAIZ / "e2e" / "package.json").is_file():
        correr([NPM, "ci"], cwd=RAIZ / "e2e")
        npx = "npx.cmd" if ES_WINDOWS else "npx"
        correr([npx, "playwright", "install", "chromium"], cwd=RAIZ / "e2e")


def up() -> None:
    """Levanta Postgres en Docker y crea la base de pruebas."""
    correr(["docker", "compose", "up", "-d", "db"])
    # Si la base de pruebas ya existe, createdb falla y esta bien.
    correr(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "createdb",
            "-U",
            "escuelita",
            "escuelita_test",
        ],
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


# Los tests del frontend corren en el huso de la escuela. Esta en tres
# lugares (aca, vite.config.ts y el workflow del CI) para que la maquina
# local y el CI no se separen: con el huso del runner, que es UTC, un
# toISOString() en lugar de la fecha local pasaba en verde.
HUSO_DE_LOS_TESTS = "America/Argentina/Buenos_Aires"


def front_test() -> None:
    """Tests del frontend (Vitest)."""
    correr([NPM, "run", "test"], cwd=FRONTEND, entorno_extra={"TZ": HUSO_DE_LOS_TESTS})


def front_dev() -> None:
    """Frontend en desarrollo."""
    correr([NPM, "run", "dev"], cwd=FRONTEND)


# --- Pruebas de punta a punta -------------------------------------------------
#
# Un navegador real contra el build servido y la API en otro origen, como en
# Render. Ver el design del change `pruebas-e2e`. Todo lo que toca la corrida
# es propio: la base `escuelita_e2e`, la API en el 8001 y el build en el 4173.
# La base de desarrollo y la API de desarrollo (8000) no se tocan nunca.

E2E = RAIZ / "e2e"
NPX = "npx.cmd" if ES_WINDOWS else "npx"
VITE = FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"
URL_E2E_POR_DEFECTO = (
    "postgresql+psycopg://escuelita:escuelita@localhost:5432/escuelita_e2e"
)
NOMBRE_BASE_E2E = "escuelita_e2e"
PUERTO_API_E2E = 8001
PUERTO_FRONT_E2E = 4173
URL_API_E2E = f"http://localhost:{PUERTO_API_E2E}"
URL_FRONT_E2E = f"http://localhost:{PUERTO_FRONT_E2E}"
# Clave de juguete: solo para que la configuracion valide. Firma tokens que
# viven lo que dura la corrida y no salen de la maquina.
CLAVE_E2E = "clave-de-juguete-del-e2e-no-se-usa-en-ningun-lado"
TOPE_DE_ARRANQUE_S = 60
ESPERAS_PROHIBIDAS = ("waitForTimeout(", "setTimeout(")

# Corre con el Python del entorno virtual, desde backend/. Recibe la URL de la
# base del E2E y la recrea, pero antes comprueba el nombre exacto y que el
# host sea local con la misma funcion que usa la semilla: una sola definicion
# de "local" en el proyecto. Si cualquiera de las dos falla, no se conecta.
_GUION_BASE_E2E = """
import sys
sys.path.insert(0, ".")
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from app.semilla import SemillaRechazada, verificar_base_local

url = make_url(sys.argv[1])
if url.database != sys.argv[2]:
    sys.exit(f"La base del E2E tiene que llamarse {sys.argv[2]!r}, no {url.database!r}. No se toco nada.")
try:
    verificar_base_local(sys.argv[1])
except SemillaRechazada:
    sys.exit("La base del E2E tiene que ser local. No se toco nada.")

mantenimiento = url.set(drivername="postgresql", database="postgres")
with psycopg.connect(mantenimiento.render_as_string(hide_password=False), autocommit=True) as conexion:
    nombre = sql.Identifier(url.database)
    # WITH (FORCE) cierra las conexiones que haya dejado una corrida cortada.
    conexion.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(nombre))
    conexion.execute(sql.SQL("CREATE DATABASE {}").format(nombre))
print("base recreada:", url.database)
"""


def _comprobar_reglas_e2e() -> None:
    """Corta si un test espera un tiempo fijo en lugar de una condicion."""
    infracciones = [
        f"  {ruta.relative_to(RAIZ)}:{numero}: {linea.strip()}"
        for ruta in sorted((E2E / "tests").rglob("*.ts"))
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1)
        if any(prohibida in linea for prohibida in ESPERAS_PROHIBIDAS)
    ]
    if infracciones:
        sys.exit(
            "Los tests E2E no esperan tiempos fijos: se espera una condicion "
            "(expect, waitForResponse).\n" + "\n".join(infracciones)
        )


def _puerto_ocupado(puerto: int) -> bool:
    import socket

    for familia, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        with socket.socket(familia, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                if s.connect_ex((host, puerto)) == 0:
                    return True
            except OSError:
                continue
    return False


def _arrancar(
    partes: list[str], cwd: Path, entorno: dict[str, str], log: Path
) -> subprocess.Popen:
    """Arranca un servicio en segundo plano, con su salida en un archivo.

    En POSIX va en su propia sesion para poder matar el grupo entero; en
    Windows se mata el arbol con taskkill (ver `_bajar`).
    """
    print(f"$ {' '.join(partes)}  (salida en {log.relative_to(RAIZ)})", flush=True)
    salida = log.open("w", encoding="utf-8")
    extra: dict = {} if ES_WINDOWS else {"start_new_session": True}
    return subprocess.Popen(
        partes, cwd=cwd, env=entorno, stdout=salida, stderr=subprocess.STDOUT, **extra
    )


def _bajar(proceso: subprocess.Popen) -> None:
    """Baja el proceso y sus hijos. El lanzador del entorno virtual en Windows
    y Node dejan hijos: matar solo al padre dejaria el puerto tomado."""
    if proceso.poll() is not None:
        return
    if ES_WINDOWS:
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proceso.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        import signal

        try:
            os.killpg(proceso.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        proceso.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proceso.kill()


def _esperar_a_que_responda(url: str, proceso: subprocess.Popen, log: Path) -> None:
    """Sondea la URL hasta que conteste. No es una espera fija: termina en
    cuanto el servicio responde, y corta antes si el proceso murio."""
    import time
    import urllib.error
    import urllib.request

    limite = time.monotonic() + TOPE_DE_ARRANQUE_S
    while time.monotonic() < limite:
        if proceso.poll() is not None:
            sys.exit(
                f"El servicio de {url} termino al arrancar. Ver {log.relative_to(RAIZ)}."
            )
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.25)
    sys.exit(
        f"{url} no respondio en {TOPE_DE_ARRANQUE_S} s. Ver {log.relative_to(RAIZ)}."
    )


def e2e() -> None:
    """Tests de punta a punta (Playwright) sobre una base propia, recreada."""
    argumentos_playwright = sys.argv[2:]
    url_base = os.environ.get("E2E_DATABASE_URL", URL_E2E_POR_DEFECTO)
    # Las variables pisan al .env: la API, Alembic y la semilla ven solo la
    # base del E2E.
    entorno_api = {
        "DATABASE_URL": url_base,
        "SECRET_KEY": CLAVE_E2E,
        "CORS_ORIGINS": URL_FRONT_E2E,
        "TZ": HUSO_DE_LOS_TESTS,
    }

    _comprobar_reglas_e2e()
    for puerto in (PUERTO_API_E2E, PUERTO_FRONT_E2E):
        if _puerto_ocupado(puerto):
            sys.exit(
                f"El puerto {puerto} ya esta en uso. El E2E no reutiliza un servicio "
                "que no levanto el: podria estar apuntando a otra base."
            )

    correr(
        [ejecutable("python"), "-c", _GUION_BASE_E2E, url_base, NOMBRE_BASE_E2E],
        cwd=BACKEND,
        entorno_extra=entorno_api,
    )
    correr(
        [ejecutable("alembic"), "upgrade", "head"],
        cwd=BACKEND,
        entorno_extra=entorno_api,
    )
    correr(
        [ejecutable("python"), str(RAIZ / "scripts" / "seed.py")],
        cwd=BACKEND,
        entorno_extra=entorno_api,
    )
    # El build como en produccion: estatico, con la API en otro origen.
    correr(
        ["node", str(VITE), "build", "--outDir", "dist/e2e", "--emptyOutDir"],
        cwd=FRONTEND,
        entorno_extra={"VITE_API_URL": URL_API_E2E},
    )

    logs = E2E / "logs"
    logs.mkdir(exist_ok=True)
    entorno = dict(os.environ)
    if BIN.is_dir():
        entorno["PATH"] = str(BIN) + os.pathsep + entorno.get("PATH", "")
    procesos: list[subprocess.Popen] = []
    codigo = 1
    try:
        log_api = logs / "api.log"
        api_e2e = _arrancar(
            [ejecutable("uvicorn"), "app.main:app", "--port", str(PUERTO_API_E2E)],
            BACKEND,
            {**entorno, **entorno_api},
            log_api,
        )
        procesos.append(api_e2e)
        log_front = logs / "front.log"
        front_e2e = _arrancar(
            [
                "node",
                str(VITE),
                "preview",
                "--outDir",
                "dist/e2e",
                "--port",
                str(PUERTO_FRONT_E2E),
                "--strictPort",
            ],
            FRONTEND,
            entorno,
            log_front,
        )
        procesos.append(front_e2e)
        _esperar_a_que_responda(f"{URL_API_E2E}/salud", api_e2e, log_api)
        _esperar_a_que_responda(f"{URL_FRONT_E2E}/", front_e2e, log_front)

        codigo = correr(
            [NPX, "playwright", "test", *argumentos_playwright],
            cwd=E2E,
            permitir_fallo=True,
            entorno_extra={"E2E_BASE_URL": URL_FRONT_E2E, "E2E_API_URL": URL_API_E2E},
        )
    finally:
        for proceso in reversed(procesos):
            _bajar(proceso)
    if codigo != 0:
        print(
            "\nEl E2E fallo. El trace de cada test esta en e2e/test-results/ "
            "(npx playwright show-trace <archivo>) y la salida de los servicios en e2e/logs/.",
            file=sys.stderr,
        )
    sys.exit(codigo)


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
    "front-test": front_test,
    "front-dev": front_dev,
    "e2e": e2e,
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
