"""Carga la temporada de demostracion. Nunca datos reales.

    python tasks.py seed

Solo invoca a `app.semilla`, que tiene los datos y las dos negativas. Este
script es el unico que hace commit. El orden importa:

1. `backend/` al path: Python agrega la carpeta del script, no el cwd.
2. Se comprueba que la base sea local antes de abrir la sesion. Importar
   `app.semilla` ya importa `app.core.db` (los modelos cuelgan de su `Base`)
   y eso crea el motor, pero `create_engine` no se conecta: la primera
   conexion la abre la sesion. Asi no llega a tocar una base remota. Si el
   entorno trae `SEMILLA_FUERA_DE_LOCAL=1` la base remota se acepta.
3. Si hubo permiso para una base remota, el aviso con sus hosts sale por
   stderr (con flush) antes de abrir la sesion.
4. Sesion, `cargar` y commit, todo en una transaccion: si algo falla a mitad
   de camino no queda una temporada a medias.

Para volver a sembrar se recrea la base: `docker compose down -v`, luego
`python tasks.py migrate` y `python tasks.py seed`.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import obtener_configuracion  # noqa: E402
from app.core.db import FabricaDeSesiones  # noqa: E402
from app.semilla import (  # noqa: E402
    CONTRASENA_DEMO,
    FAMILIAS,
    USUARIOS,
    SemillaRechazada,
    cargar,
    comprobar_destino,
)


def main() -> None:
    try:
        # El permiso se lee del entorno real del proceso, no de la configuracion.
        aviso = comprobar_destino(obtener_configuracion().database_url, os.environ)
        if aviso:
            print(aviso, file=sys.stderr, flush=True)

        # Recien aca se abre la primera conexion.
        with FabricaDeSesiones() as sesion:
            cargar(sesion)
            sesion.commit()
    except SemillaRechazada as error:
        print(error, file=sys.stderr)
        sys.exit(1)

    print(
        f"Semilla cargada: temporada 2026-27 y {len(FAMILIAS)} familias de ejemplo. "
        "Usuarios de demostracion:"
    )
    for username, _nombre, _apellido, rol in USUARIOS:
        print(f"  {username:<12} {rol.value:<12} contraseña: {CONTRASENA_DEMO}")


if __name__ == "__main__":
    main()
