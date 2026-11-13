from fastapi import APIRouter

from app.api.v1 import alumnos, auth, familias, grupos, personas

# Cada capability agrega su router aca. Un router por capability, nunca
# endpoints colgados del router principal.
router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(grupos.router)
router.include_router(familias.router)
router.include_router(personas.router)
router.include_router(alumnos.router)
