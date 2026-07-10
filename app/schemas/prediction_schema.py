from pydantic import BaseModel


class PredictionResponse(BaseModel):
    match_id: int

    home_win_probability: float
    draw_probability: float
    away_win_probability: float

    confidence_score: float
    risk_level: str

    expected_home_goals: float
    expected_away_goals: float

    reasoning: list[str]