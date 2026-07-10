from pydantic import BaseModel
from datetime import datetime


class MatchCreate(BaseModel):
    home_team_id: int
    away_team_id: int
    league: str | None = None
    season: str | None = None
    kickoff_time: datetime | None = None


class MatchResponse(MatchCreate):
    id: int
    status: str

    class Config:
        from_attributes = True