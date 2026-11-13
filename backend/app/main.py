from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.api.v1.router import router as router_v1
from app.core.config import obtener_configuracion
from app.core.errores import ReglaIncumplida


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


@app.exception_handler(RequestValidationError)
async def error_de_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    # El mismo 422 que FastAPI pero sin `input`: no repite lo recibido (una
    # contrasena rechazada, un surrogate que no se puede codificar).
    errores = [
        {clave: valor for clave, valor in e.items() if clave != "input"} for e in exc.errors()
    ]
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(errores)},
    )


@app.exception_handler(ReglaIncumplida)
async def regla_incumplida(_: Request, exc: ReglaIncumplida) -> JSONResponse:
    # La forma del 422 de validacion, con `type` propio y sin ningun otro
    # campo: la pantalla pega cada `msg` junto a su campo.
    errores = [
        {"loc": ["body", *ubicacion], "msg": mensaje, "type": "regla_de_negocio"}
        for ubicacion, mensaje in exc.errores
    ]
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errores})


app.include_router(router_v1)


@app.get("/salud", tags=["infraestructura"])
def salud() -> dict[str, str]:
    return {"estado": "ok"}
