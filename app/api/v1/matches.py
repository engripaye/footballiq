from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match import Match
from app.models.team import Team
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
def get_matches(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return db.query(Match).order_by(Match.kickoff_time).offset(offset).limit(limit).all()


@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    home = db.query(Team).filter(Team.id == match.home_team_id).first()
    away = db.query(Team).filter(Team.id == match.away_team_id).first()
    return {"id": match.id, "league": match.league, "season": match.season,
            "kickoff_time": match.kickoff_time, "status": match.status,
            "home_team": home, "away_team": away}
