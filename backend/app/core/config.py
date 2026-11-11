from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Lo que el entorno aporta. Nada de esto tiene valor por defecto en
    produccion: si falta, la aplicacion no arranca, que es mejor que
    arrancar con una clave de ejemplo."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str = ""
    secret_key: str
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
