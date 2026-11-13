"""Rutas de alumnos. Solo traducen el resultado de app/services/alumnos.py a
HTTP."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import obtener_sesion
from app.core.deps import MENSAJE_SESION_INVALIDA, exigir_rol
from app.models.usuario import RolUsuario, Usuario
from app.schemas.alumnos import (
    AltaAlumnoEntrada,
    AlumnoRegistrado,
    FamiliaDelAlumno,
    InscripcionDelAlumno,
)
from app.schemas.errores import ErroresDeCampo, respuesta_de_error
from app.services.alumnos import GrupoAjeno, registrar_alumno

router = APIRouter(prefix="/alumnos", tags=["alumnos"])

MENSAJE_GRUPO_AJENO = "Solo podés inscribir alumnos en tus grupos."

# Validacion y reglas del alta comparten la forma; las reglas llevan `type`
# `regla_de_negocio`.
_RESPUESTA_422: dict[str, Any] = {
    "model": ErroresDeCampo,
    "description": (
        "Datos invalidos o una regla del alta incumplida (grupo, familia, "
        "personas). Cada error trae su campo en `loc`."
    ),
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AlumnoRegistrado,
    responses={
        status.HTTP_401_UNAUTHORIZED: respuesta_de_error(MENSAJE_SESION_INVALIDA),
        status.HTTP_403_FORBIDDEN: respuesta_de_error(MENSAJE_GRUPO_AJENO),
        status.HTTP_422_UNPROCESSABLE_ENTITY: _RESPUESTA_422,
    },
)
def registrar(
    entrada: AltaAlumnoEntrada,
    usuario: Annotated[
        Usuario,
        Depends(exigir_rol(RolUsuario.ADMIN, RolUsuario.COORDINADOR, RolUsuario.PROFESOR)),
    ],
    sesion: Annotated[Session, Depends(obtener_sesion)],
) -> AlumnoRegistrado:
    # El permiso del Profesor sobre el grupo lo resuelve el servicio: el
    # grupo viene en el cuerpo (design, «El alta, en un servicio...»).
    try:
        alta = registrar_alumno(sesion, usuario, entrada)
    except GrupoAjeno:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_GRUPO_AJENO
        ) from None
    return AlumnoRegistrado(
        id=alta.alumno.id,
        nombre=alta.alumno.nombre,
        apellido=alta.alumno.apellido,
        fecha_nacimiento=alta.alumno.fecha_nacimiento,
        familia=FamiliaDelAlumno(
            id=alta.familia.id, etiqueta=alta.etiqueta, categoria=alta.familia.categoria
        ),
        inscripcion=InscripcionDelAlumno(
            grupo_id=alta.grupo.id,
            grupo_nombre=alta.grupo.nombre,
            turno=alta.grupo.turno,
            temporada_id=alta.grupo.temporada_id,
        ),
    )
