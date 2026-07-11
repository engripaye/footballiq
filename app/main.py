from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import api_router
import app.models.injury, app.models.league, app.models.match, app.models.odds, app.models.player, app.models.prediction, app.models.team
from app.seed import seed_demo_data
from app.core.schema_upgrade import upgrade_legacy_schema

Base.metadata.create_all(bind=engine)
upgrade_legacy_schema(engine)
if settings.SEED_DEMO_DATA:
    seed_demo_data()

app = FastAPI(
    title=settings.APP_NAME,
    description="FootballIQ - AI Football Prediction Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to FootballIQ Backend",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }
