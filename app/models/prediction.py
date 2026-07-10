from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from datetime import datetime
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(Integer, ForeignKey('matches.id', ondelete="CASCADE"), nullable=False, index=True)

    home_win_probability = Column(Float, nullable=False)
    draw_probability = Column(Float, nullable=False)
    away_win_probability = Column(Float, nullable=False)

    confidence_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    expected_home_goals = Column(Float, nullable=False)
    expected_away_goals = Column(Float, nullable=False)

    reasoning = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
