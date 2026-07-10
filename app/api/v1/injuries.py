from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.injury import Injury
from app.schemas.injury_schema import InjuryCreate, InjuryResponse

router = APIRouter(prefix="/injuries", tags=["Injuries"])


@router.post("/", response_model=InjuryResponse)
def create_injury(payload: InjuryCreate, db: Session = Depends(get_db)):
    injury = Injury(**payload.model_dump())
    db.add(injury)
    db.commit()
    db.refresh(injury)
    return injury


@router.get("/", response_model=list[InjuryResponse])
def get_injuries(db: Session = Depends(get_db)):
    return db.query(Injury).all()