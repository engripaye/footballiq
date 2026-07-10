from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.prediction_engine import PredictionEngine
from app.schemas.prediction_schema import PredictionResponse

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/{match_id}", response_model=PredictionResponse)
def predict_match(match_id: int, db: Session = Depends(get_db)):
    try:
        return PredictionEngine.predict_match(db=db, match_id=match_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))