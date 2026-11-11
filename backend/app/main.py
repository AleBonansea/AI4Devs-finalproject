from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as router_v1
from app.core.config import obtener_configuracion


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    # FastAPI moderno usa `lifespan`, no `@app.on_event`.
    yield


app = FastAPI(
    title="Escuelita de Verano",
    description="API de administracion de la escuelita de verano del club sede.",
    version="0.1.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_configuracion().origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_v1)


@app.get("/salud", tags=["infraestructura"])
def salud() -> dict[str, str]:
    return {"estado": "ok"}
