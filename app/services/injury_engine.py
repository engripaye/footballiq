from sqlalchemy.orm import Session
from app.models.injury import Injury


class InjuryEngine:

    @staticmethod
    def calculate_team_injury_impact(db: Session, team_id: int) -> float:
        injuries = (
            db.query(Injury)
            .filter(Injury.team_id == team_id)
            .filter(Injury.is_active == True)
            .all()
        )

        if not injuries:
            return 0.0

        total_impact = sum(injury.impact_score for injury in injuries)

        return min(total_impact, 30.0)