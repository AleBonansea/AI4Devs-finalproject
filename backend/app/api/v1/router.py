from fastapi import APIRouter

from app.api.v1 import auth, grupos

# Cada capability agrega su router aca. Un router por capability, nunca
# endpoints colgados del router principal.
router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(grupos.router)
