"""Corta los comandos que destruyen datos en la base.

ESTO ES UNA RED, NO UN CANDADO.
Mira el texto del comando. Quien quiera saltearlo lo saltea: basta con
escribir el DROP dentro de un script de Python y ejecutar el script.
El candado de verdad es que el rol de base de datos del entorno de
desarrollo no tenga permiso para borrar, y que produccion no sea
alcanzable desde aca. Esto es la red que evita el accidente, no el
ataque.

Deja pasar `alembic downgrade -1`: revertir la ultima migracion es
trabajo normal. Corta `downgrade base`, que vacia el esquema entero.
"""

import json
import re
import sys

PROHIBIDO = [
    (r"alembic\s+downgrade\s+base", "`alembic downgrade base` tira el esquema entero. Para revertir la ultima migracion usa `alembic downgrade -1`."),
    (r"drop\s+(table|database|schema)", "DROP destruye datos. Si el esquema tiene que cambiar, va por una migracion de Alembic con su reverso."),
    (r"\btruncate\b", "TRUNCATE vacia la tabla. Si necesitas datos limpios, usa `make seed` sobre una base de pruebas."),
    (r"docker\s+compose\s+down[^\n]*(-v|--volumes)", "`down -v` borra el volumen de Postgres y con el toda la base local."),
    (r"\bdropdb\b", "dropdb destruye la base completa."),
    (r"rm\s+(-\w+\s+)*[^\n]*alembic/versions", "Las migraciones aplicadas no se borran: se revierten con una migracion nueva."),
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
            print("Si de verdad hace falta, lo corre una persona a mano fuera de Claude.", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
