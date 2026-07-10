from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)

    name = Column(String, nullable=False)
    position = Column(String, nullable=False)


