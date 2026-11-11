import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Importar el paquete de modelos es lo que llena Base.metadata. Sin esto,
# --autogenerate cree que no hay tablas y propone borrarlas todas.
import app.models  # noqa: F401
from alembic import context
from app.core.config import obtener_configuracion
from app.core.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ALEMBIC_URL permite apuntar a la base de pruebas sin tocar el .env.
url = os.environ.get("ALEMBIC_URL") or obtener_configuracion().database_url
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectable.connect() as conexion:
        context.configure(
            connection=conexion,
            target_metadata=target_metadata,
            # Sin esto, un cambio de tipo (numeric(10,2) -> numeric(12,2))
            # pasa inadvertido, y en columnas de dinero eso trunca importes.
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
