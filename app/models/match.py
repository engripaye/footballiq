from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    league = Column(String, nullable=False)
    season = Column(String, nullable=False)
    kickoff_time = Column(String, nullable=False)

    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)

    home_xg = Column(Float, default=0.0)
    away_xg = Column(Float, default=0.0)

    status = Column(String, default="scheduled")