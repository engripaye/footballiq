from pydantic import BaseModel


class InjuryCreate(BaseModel):
    player_id: int
    team_id: int
    injury_type: str | None = None
    severity: str = "medium"
    impact_score: float = 0
    expected_absence_days: int = 0


class InjuryResponse(InjuryCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True