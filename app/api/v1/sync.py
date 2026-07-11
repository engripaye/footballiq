from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.providers.football_data_provider import FootballDataOrgProvider
from app.services.fixture_sync_service import FixtureSyncService

router = APIRouter(prefix="/sync", tags=["Data Synchronization"])


@router.get("/status")
def sync_status():
    return {
        "enabled": settings.FIXTURE_SYNC_ENABLED,
        "provider": "football-data.org",
        "configured": bool(settings.FOOTBALL_DATA_API_KEY),
        "base_url": settings.FOOTBALL_DATA_BASE_URL,
    }


@router.post("/competitions/{competition_code}")
def sync_competition(
    competition_code: str,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not settings.FIXTURE_SYNC_ENABLED:
        raise HTTPException(status_code=503, detail="Fixture synchronization is disabled")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from cannot be later than date_to")
    try:
        provider = FootballDataOrgProvider()
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    try:
        return FixtureSyncService(db, provider).sync_competition(competition_code.upper(), date_from, date_to)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Unable to synchronize fixtures: {error}") from error
    finally:
        provider.close()
