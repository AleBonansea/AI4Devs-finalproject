"""Corta los comandos que sacarian datos reales del proyecto hacia afuera.

El sistema guarda datos de salud y documentos de identidad de menores
(Ley 25.326). Un volcado de la base subido a cualquier parte, aunque sea
para depurar, es una filtracion.

Igual que el otro hook: esto es una red, no un candado. Evita el
descuido, no al que quiera esquivarlo.
"""

import json
import re
import sys

PROHIBIDO = [
    (r"pg_dump", "Un volcado de la base puede tener datos medicos y documentos de menores. Si necesitas datos para probar, usa `make seed`."),
    (r"curl[^\n]*(-T|--upload-file|-d\s*@|--data-binary\s*@|-F\s*\S*=@)", "Eso sube el contenido de un archivo a un servidor. No se sacan archivos del proyecto."),
    (r"(cat|type|head|tail)\s+[^\n|]*\.env[^\n]*\|", "El `.env` tiene las credenciales. No se encadena a otro comando."),
    (r"\.env[^\n]*\|\s*(curl|wget|nc|ncat)", "El `.env` tiene las credenciales. No sale del equipo."),
    (r"(uploads|documentos)[^\n]*\|\s*(curl|wget|nc|base64)", "Los documentos adjuntos son DNI y fichas medicas de menores. No se copian ni se codifican para sacarlos."),
    (r"\bnc\s+[^\n]*\s\d+\s*<", "Eso manda el contenido de un archivo por la red."),
]


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0

    comando = (datos.get("tool_input") or {}).get("command", "")
    if not comando:
        return 0

    plano = comando.lower()
    for patron, motivo in PROHIBIDO:
        if re.search(patron, plano):
            print(f"Comando bloqueado: {motivo}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
