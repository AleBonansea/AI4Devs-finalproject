"""Rutas de cargos. Solo traducen el resultado de app/services/cargos.py a
HTTP. Solo el Admin: el rol se resuelve antes de leer el cuerpo."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, MENSAJE_SIN_PERMISO, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.cargos import CargoEntrada, CargoRegistrado, CargoSimulado, OpcionesDeCargo
from app.schemas.errores import ErroresDeCampo, respuesta_de_error
from app.schemas.pagos import PagoEntrada, PagoRegistrado
from app.services.cargos import ConflictoDeCargo, registrar_cargo, simular_cargo
from app.services.opciones_cargo import obtener_opciones_de_cargo
from app.services.pagos import CargoInexistente, ConflictoDePago, registrar_pago

router = APIRouter(prefix="/cargos", tags=["cargos"])

_RESPUESTA_409 = respuesta_de_error(
    "El alumno ya tiene un cargo «Abono» de «Mes 1» en el turno mañana."
)
_RESPUESTA_422: dict[str, Any] = {
    "model": ErroresDeCampo,
    "description": (
        "Datos inválidos o una regla del cargo incumplida. Cada error trae su campo en `loc`."
    ),
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CargoRegistrado,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
        status.HTTP_409_CONFLICT: _RESPUESTA_409,
        status.HTTP_422_UNPROCESSABLE_ENTITY: _RESPUESTA_422,
    },
)
def registrar(
    entrada: CargoEntrada,
    usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> CargoRegistrado:
    try:
        return registrar_cargo(sesion, usuario, entrada)
    except ConflictoDeCargo as conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflicto.mensaje
        ) from None


@router.get(
    "/opciones",
    response_model=OpcionesDeCargo,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
    },
)
def opciones(
    _usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> OpcionesDeCargo:
    """Tipos de cargo y períodos de la temporada vigente."""
    return obtener_opciones_de_cargo(sesion)


@router.post(
    "/simulacion",
    response_model=CargoSimulado,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
        status.HTTP_409_CONFLICT: _RESPUESTA_409,
        status.HTTP_422_UNPROCESSABLE_ENTITY: _RESPUESTA_422,
    },
)
def simular(
    entrada: CargoEntrada,
    _usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> CargoSimulado:
    try:
        return simular_cargo(sesion, entrada)
    except ConflictoDeCargo as conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflicto.mensaje
        ) from None


@router.post(
    "/{cargo_id}/pagos",
    status_code=status.HTTP_201_CREATED,
    response_model=PagoRegistrado,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_SIN_PERMISO),
        status.HTTP_404_NOT_FOUND: respuesta_de_error("El cargo no existe."),
        status.HTTP_409_CONFLICT: respuesta_de_error("El cargo ya está saldado."),
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErroresDeCampo,
            "description": "Monto o fecha inválidos, o monto mayor que el saldo del cargo.",
        },
    },
)
def pagar(
    cargo_id: int,
    entrada: PagoEntrada,
    usuario: Annotated[Usuario, Depends(exigir_rol(RolUsuario.ADMIN))],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> PagoRegistrado:
    """Registra un pago del cargo y su ingreso en tesorería. Solo el Admin."""
    try:
        return registrar_pago(sesion, usuario, cargo_id, entrada)
    except CargoInexistente as inexistente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(inexistente)
        ) from None
    except ConflictoDePago as conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflicto.mensaje
        ) from None
