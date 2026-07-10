from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.intelligence_engine import IntelligenceEngine

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/{match_id}")
def match_intelligence(match_id: int, db: Session = Depends(get_db)):
    try:
        return IntelligenceEngine.build_report(db, match_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
