from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match import Match
from app.schemas.match_schema import MatchCreate, MatchResponse

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/", response_model=MatchResponse)
def create_match(payload: MatchCreate, db: Session = Depends(get_db)):
    match = Match(**payload.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/", response_model=list[MatchResponse])
def get_matches(db: Session = Depends(get_db)):
    return db.query(Match).all()