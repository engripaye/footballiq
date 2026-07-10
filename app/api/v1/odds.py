from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.odds import Odds
from app.schemas.odds_schema import OddsCreate, OddsResponse

router = APIRouter(prefix="/odds", tags=["Odds"])


@router.post("/", response_model=OddsResponse)
def create_odds(payload: OddsCreate, db: Session = Depends(get_db)):
    odds = Odds(**payload.model_dump())
    db.add(odds)
    db.commit()
    db.refresh(odds)
    return odds


@router.get("/", response_model=list[OddsResponse])
def get_odds(db: Session = Depends(get_db)):
    return db.query(Odds).all()