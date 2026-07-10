from pydantic import BaseModel


class OddsCreate(BaseModel):
    match_id: int
    bookmaker: str
    home_win_odds: float
    draw_odds: float
    away_win_odds: float


class OddsResponse(OddsCreate):
    id: int

    class Config:
        from_attributes = True