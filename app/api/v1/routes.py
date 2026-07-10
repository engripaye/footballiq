from fastapi import APIRouter

from app.api.v1.teams import router as teams_router
from app.api.v1.matches import router as matches_router
from app.api.v1.injuries import router as injuries_router
from app.api.v1.odds import router as odds_router
from app.api.v1.predictions import router as predictions_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(teams_router)
api_router.include_router(matches_router)
api_router.include_router(injuries_router)
api_router.include_router(odds_router)
api_router.include_router(predictions_router)