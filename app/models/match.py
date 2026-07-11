from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, nullable=True, unique=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="SET NULL"), nullable=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    league = Column(String, nullable=False)
    season = Column(String, nullable=False)
    kickoff_time = Column(DateTime, nullable=False)

    home_goals = Column(Integer, nullable=True)
    away_goals = Column(Integer, nullable=True)

    home_xg = Column(Float, default=0.0)
    away_xg = Column(Float, default=0.0)

    status = Column(String, default="scheduled")
    matchday = Column(Integer, nullable=True)
    stage = Column(String(100), nullable=True)
    group_name = Column(String(100), nullable=True)
    half_time_home_goals = Column(Integer, nullable=True)
    half_time_away_goals = Column(Integer, nullable=True)
    venue = Column(String(200), nullable=True)
    referee = Column(String(150), nullable=True)

    __table_args__ = (
        UniqueConstraint("home_team_id", "away_team_id", "kickoff_time", name="uq_match_teams_kickoff"),
    )
