"""Corta los colores a pelo en el frontend.

Un agente sin catalogo inventa un gris nuevo cada vez. A los dos meses hay
catorce grises y ninguno es el del sistema. Los colores salen del tema, con
nombre.

Solo mira `frontend/src/`, y deja pasar los archivos de PERMITIDOS, que son
donde los valores reales tienen que vivir. La lista es de rutas exactas, no
de nombres parecidos: con coincidencia por nombre, cualquier
`ayudanteDeTema.tsx` quedaba exento sin motivo.
"""

import json
import os
import re
import sys

PATRON = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(")
EXTENSIONES = (".ts", ".tsx", ".js", ".jsx", ".css")

# El catalogo. Un archivo nuevo aca es una decision, no un descuido: si el
# tema se parte en varios, se agregan a mano.
PERMITIDOS = (
    "frontend/src/tema.ts",
    "frontend/src/index.css",
)


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0

    ruta = ((datos.get("tool_input") or {}).get("file_path", "") or "").replace("\\", "/")
    if "frontend/src/" not in ruta or not ruta.endswith(EXTENSIONES):
        return 0
    if any(ruta.endswith(p) for p in PERMITIDOS):
        return 0
    if not os.path.exists(ruta):
        return 0

    try:
        with open(ruta, encoding="utf-8") as f:
            lineas = f.readlines()
    except Exception:
        return 0

    hallazgos = [
        f"  linea {i}: {linea.strip()[:90]}"
        for i, linea in enumerate(lineas, 1)
        if PATRON.search(linea)
    ]
    if not hallazgos:
        return 0

    print(f"Colores a pelo en {ruta}:", file=sys.stderr)
    print("\n".join(hallazgos[:10]), file=sys.stderr)
    print(
        "\nUsa un nombre del tema: theme.palette, sx o la constante `colores`"
        "\nde frontend/src/tema.ts. Si el color que necesitas no existe, agregalo"
        "\nahi con un nombre que diga PARA QUE sirve (`deuda`, no `rojo`), y"
        "\ndespues usalo aca.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
