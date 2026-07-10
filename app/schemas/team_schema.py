from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    country: str
    league: str
    elo_rating: float = 1500
    attacking_strength: float = 1.0
    defense_strength: float = 1.0
    form_score: float = 50


class TeamResponse(TeamCreate):
    id: int

    class Config:
        from_attributes = True
