"""Formatea el archivo recien escrito.

**Esto es comodidad, no un guardarrail.** Lo que corta de verdad es
`ruff format --check` en el CI, y el paso 5 de la skill backend-feature,
que formatea los tests antes de congelarlos.

Historia de por que esta escrito asi: la primera version llamaba a
`ruff` a secas y envolvia todo en `except Exception: pass`. Como ruff
vive dentro del entorno virtual y no en el PATH suelto, tiraba
FileNotFoundError en cada archivo y se lo comia. Nunca formateo nada y
nunca lo dijo, durante semanas. Un hook que no hace nada y ademas oculta
que no hace nada es peor que no tenerlo: ocupa lugar y da sensacion de
cobertura.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent


def _buscar(nombre: str, *carpetas: Path) -> str | None:
    """Busca el ejecutable dentro del entorno virtual, y si no, en el PATH."""
    for carpeta in carpetas:
        for sufijo in ("", ".exe", ".cmd"):
            ruta = carpeta / (nombre + sufijo)
            if ruta.is_file():
                return str(ruta)
    from shutil import which

    return which(nombre)


def _ruff() -> str | None:
    venv = RAIZ / "backend" / ".venv"
    return _buscar("ruff", venv / "Scripts", venv / "bin")


def _correr(partes: list[str]) -> None:
    try:
        subprocess.run(partes, capture_output=True, timeout=30, check=False, cwd=RAIZ)
    except Exception:
        pass


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0

    ruta = (datos.get("tool_input") or {}).get("file_path", "")
    if not ruta or not os.path.exists(ruta):
        return 0

    if ruta.endswith(".py"):
        ruff = _ruff()
        if ruff is None:
            # Silencioso a proposito: en un clon recien hecho, antes de
            # `pip install -e ".[dev]"`, no hay ruff y no es un error.
            # Lo que no puede volver a pasar es que exista y no lo encuentre.
            return 0
        _correr([ruff, "format", ruta])
        _correr([ruff, "check", "--fix", ruta])
    elif ruta.endswith((".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".md")):
        _correr(["npx", "--no-install", "prettier", "--write", ruta])

    return 0


if __name__ == "__main__":
    sys.exit(main())
