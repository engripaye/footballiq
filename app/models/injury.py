from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from app.core.database import Base

class Injury(Base):
    __tablename__ = "injuries"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    injury_type = Column(String, nullable=True)
    severity = Column(String, default="medium")

    impact_score = Column(Float, default=0.0)
    expected_absence_days = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)