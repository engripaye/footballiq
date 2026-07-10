from pydantic import BaseModel
from datetime import datetime


class MatchCreate(BaseModel):
    home_team_id: int
    away_team_id: int
    league: str
    season: str
    kickoff_time: datetime


class MatchResponse(MatchCreate):
    id: int
    status: str

    class Config:
        from_attributes = True
