from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, nullable=True, unique=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=False)
    league = Column(String, nullable=False)
    short_name = Column(String(100), nullable=True)
    abbreviation = Column(String(20), nullable=True)
    crest_url = Column(String(500), nullable=True)
    stadium = Column(String(150), nullable=True)

    elo_rating = Column(Float, default=1500)
    attacking_strength = Column(Float, default=1.0)
    defense_strength = Column(Float, default=1.0)

    form_score = Column(Float, default=50.0)
