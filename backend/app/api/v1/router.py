from fastapi import APIRouter

# Cada capability agrega su router aca. Un router por capability, nunca
# endpoints colgados del router principal.
router = APIRouter(prefix="/api/v1")
