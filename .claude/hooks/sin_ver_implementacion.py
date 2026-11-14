"""Corta el acceso del test-writer a la implementacion.

Va en el frontmatter de `.claude/agents/test-writer.md` como PreToolUse,
asi que solo corre dentro de ese agente. Sale con 2, que es el codigo que
bloquea la herramienta (cualquier otro codigo distinto de cero es un
error que no bloquea y la herramienta corre igual).

Read, Write, Edit y NotebookEdit: mira la ruta resuelta. Grep y Glob, lo
mismo, y se cortan tambien si buscan desde una carpeta que CONTIENE la
implementacion (la raiz del repo, backend/, frontend/), porque si no un
Grep sin ruta la recorre entera.

Bash: mira el texto del comando. Ahi es una red, no un candado: corta
`cat backend/app/main.py`, pero no un script que arme la ruta por partes.

Falla cerrado: si la entrada no se puede leer o tiene una forma que no
espera, bloquea. Un candado que se abre cuando se rompe no es un candado.
Lo unico que no puede cubrir es que `python` no este en el PATH: ahi el
hook ni arranca y la herramienta corre.
"""

import json
import os
import re
import sys

# `frontend/dist` es el bundle compilado de `frontend/src`: leerlo es leer
# la implementacion con otro formato.
PROTEGIDAS = (
    "backend/app",
    "backend/alembic/versions",
    "frontend/src",
    "frontend/dist",
)

MOTIVO = (
    "CANDADO test-writer: {que} toca la implementacion ({ruta}). "
    "El test-writer escribe los tests desde la spec, sin ver el codigo."
)


def normalizar(ruta: str, cwd: str) -> str:
    """Ruta absoluta, con barras normales y en minusculas (Windows)."""
    if not os.path.isabs(ruta):
        ruta = os.path.join(cwd, ruta)
    return os.path.normpath(ruta).replace("\\", "/").lower().rstrip("/")


def raiz_del_repo(cwd: str) -> str:
    """La carpeta del repo: la que contiene .claude/, subiendo desde cwd."""
    actual = os.path.abspath(cwd)
    while True:
        if os.path.isdir(os.path.join(actual, ".claude")):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:
            return os.path.abspath(cwd)
        actual = padre


def protegidas_absolutas(raiz: str) -> list[str]:
    return [normalizar(p, raiz) for p in PROTEGIDAS]


def dentro_de(ruta: str, carpeta: str) -> bool:
    return ruta == carpeta or ruta.startswith(carpeta + "/")


def revisar_ruta(ruta: str, cwd: str, raiz: str, es_busqueda: bool) -> str | None:
    """Devuelve la carpeta protegida afectada, o None si la ruta es libre."""
    absoluta = normalizar(ruta, cwd)
    for carpeta in protegidas_absolutas(raiz):
        if dentro_de(absoluta, carpeta):
            return carpeta
        # Una busqueda desde una carpeta que contiene a la protegida la recorre.
        if es_busqueda and dentro_de(carpeta, absoluta):
            return carpeta
    return None


def revisar_patron(patron: str) -> str | None:
    """Un glob como `backend/app/**` apunta a la implementacion aunque la ruta no."""
    plano = patron.replace("\\", "/").lower()
    for carpeta in PROTEGIDAS:
        if carpeta in plano:
            return carpeta
    return None


def revisar_comando(comando: str) -> str | None:
    plano = comando.replace("\\", "/").lower()
    plano = re.sub(r"/+", "/", plano)
    for carpeta in PROTEGIDAS:
        if carpeta in plano:
            return carpeta
    return None


def revisar(datos: dict) -> str | None:
    """Devuelve la carpeta protegida que toca la llamada, o None si es libre."""
    herramienta = datos.get("tool_name", "")
    entrada = datos.get("tool_input") or {}
    cwd = datos.get("cwd") or os.getcwd()
    raiz = raiz_del_repo(cwd)

    hallazgo: str | None = None
    if herramienta in ("Read", "Write", "Edit"):
        hallazgo = revisar_ruta(
            entrada.get("file_path", ""), cwd, raiz, es_busqueda=False
        )
    elif herramienta == "NotebookEdit":
        hallazgo = revisar_ruta(
            entrada.get("notebook_path", ""), cwd, raiz, es_busqueda=False
        )
    elif herramienta in ("Grep", "Glob"):
        hallazgo = revisar_ruta(entrada.get("path") or cwd, cwd, raiz, es_busqueda=True)
        hallazgo = hallazgo or revisar_patron(entrada.get("glob", "") or "")
        if herramienta == "Glob":
            hallazgo = hallazgo or revisar_patron(entrada.get("pattern", "") or "")
    elif herramienta == "Bash":
        hallazgo = revisar_comando(entrada.get("command", ""))
    return hallazgo


def main() -> int:
    try:
        datos = json.load(sys.stdin)
        hallazgo = revisar(datos)
    except Exception as error:
        # Falla cerrado: una entrada que no se entiende no se deja pasar.
        print(
            f"CANDADO test-writer: el hook no pudo revisar la llamada ({error!r}).",
            file=sys.stderr,
        )
        return 2

    if hallazgo:
        print(
            MOTIVO.format(que=datos.get("tool_name", ""), ruta=hallazgo),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
