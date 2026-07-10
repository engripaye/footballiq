from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    country = Column(String, nullable=False)
    league = Column(String, nullable=False)

    elo_rating = Column(Float, default=1500)
    attacking_strength = Column(Float, default=1.0)
    defense_strength = Column(Float, default=1.0)

    form_score = Column(Float, default=50.0)
