"""Carga la temporada de demostracion. Nunca datos reales.

    python tasks.py seed

Solo invoca a `app.semilla`, que tiene los datos y las dos negativas. Este
script es el unico que hace commit. El orden importa:

1. `backend/` al path: Python agrega la carpeta del script, no el cwd.
2. Se comprueba que la base sea local antes de abrir la sesion. Importar
   `app.semilla` ya importa `app.core.db` (los modelos cuelgan de su `Base`)
   y eso crea el motor, pero `create_engine` no se conecta: la primera
   conexion la abre la sesion. Asi no llega a tocar una base remota.
3. Sesion, `cargar` y commit, todo en una transaccion: si algo falla a mitad
   de camino no queda una temporada a medias.

Para volver a sembrar se recrea la base: `docker compose down -v`, luego
`python tasks.py migrate` y `python tasks.py seed`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.config import obtener_configuracion  # noqa: E402
from app.core.db import FabricaDeSesiones  # noqa: E402
from app.semilla import (  # noqa: E402
    CONTRASENA_DEMO,
    USUARIOS,
    SemillaRechazada,
    cargar,
    verificar_base_local,
)


def main() -> None:
    try:
        verificar_base_local(obtener_configuracion().database_url)

        # Recien aca se abre la primera conexion.
        with FabricaDeSesiones() as sesion:
            cargar(sesion)
            sesion.commit()
    except SemillaRechazada as error:
        print(error, file=sys.stderr)
        sys.exit(1)

    print("Semilla cargada: temporada 2026-27. Usuarios de demostracion:")
    for username, _nombre, _apellido, rol in USUARIOS:
        print(f"  {username:<12} {rol.value:<12} contraseña: {CONTRASENA_DEMO}")


if __name__ == "__main__":
    main()
