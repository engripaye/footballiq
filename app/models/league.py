from sqlalchemy import Boolean, Column, Integer, String

from app.core.database import Base


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, nullable=False, unique=True, index=True)
    provider_code = Column(String(20), nullable=True, unique=True, index=True)
    name = Column(String(150), nullable=False)
    country = Column(String(100), nullable=True)
    emblem_url = Column(String(500), nullable=True)
    current_season = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
