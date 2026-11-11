"""Formatea el archivo recien escrito. Nunca falla la operacion.

Si la herramienta no esta instalada o el archivo todavia no es valido,
el hook calla y sigue: formatear es comodidad, no un guardarrail.
Lo que corta de verdad es `make lint` en CI.
"""

import json
import os
import subprocess
import sys


def correr(partes: list[str]) -> None:
    try:
        subprocess.run(partes, capture_output=True, timeout=30, check=False)
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
        correr(["ruff", "format", ruta])
        correr(["ruff", "check", "--fix", ruta])
    elif ruta.endswith((".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".md")):
        correr(["npx", "--no-install", "prettier", "--write", ruta])

    return 0


if __name__ == "__main__":
    sys.exit(main())
