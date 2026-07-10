from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base

class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)

    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)

    bookmaker = Column(String, nullable=False)
    home_win_odds = Column(Float, nullable=False)
    draw_odds = Column(Float, nullable=False)
    away_win_odds = Column(Float, nullable=False)
