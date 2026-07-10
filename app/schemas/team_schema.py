from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    country: str | None = None
    league: str | None = None
    elo_rating: float = 1500
    attack_strength: float = 1.0
    defense_strength: float = 1.0
    form_score: float = 50


class TeamResponse(TeamCreate):
    id: int

    class Config:
        from_attributes = True