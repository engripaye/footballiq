from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import api_router
import app.models.injury, app.models.league, app.models.match, app.models.odds, app.models.player, app.models.prediction, app.models.team
from app.seed import seed_demo_data
from app.core.schema_upgrade import upgrade_legacy_schema
from app.services.bootstrap_sync_service import sync_provider_data_if_empty

Base.metadata.create_all(bind=engine)
upgrade_legacy_schema(engine)
if settings.SEED_DEMO_DATA:
    seed_demo_data()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if (
        settings.APP_ENV.lower() == "production"
        and settings.AUTO_SYNC_ON_STARTUP
        and settings.FIXTURE_SYNC_ENABLED
        and settings.FOOTBALL_DATA_API_KEY
    ):
        Thread(target=sync_provider_data_if_empty, name="football-data-bootstrap", daemon=True).start()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="FootballIQ - AI Football Prediction Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
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
