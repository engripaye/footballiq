from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.team import Team
from app.schemas.team_schema import TeamCreate, TeamResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/", response_model=TeamResponse)
def create_team(payload: TeamCreate, db: Session = Depends(get_db)):
    team = Team(**payload.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/", response_model=list[TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()