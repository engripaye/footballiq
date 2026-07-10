from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="FootballIQ - AI Football Prediction Intelligence Platform",
    version="1.0.0"
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