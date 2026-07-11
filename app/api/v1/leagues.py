from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.league import League
from app.models.match import Match
from app.models.team import Team

router = APIRouter(prefix="/leagues", tags=["Leagues"])

COMPETITION_AREAS = {
    "PL": "England", "ELC": "England", "PD": "Spain", "BL1": "Germany",
    "SA": "Italy", "FL1": "France", "DED": "Netherlands", "PPL": "Portugal",
    "BSA": "Brazil", "CL": "Europe", "EC": "Europe", "WC": "World",
}


@router.get("/")
def get_leagues(db: Session = Depends(get_db)):
    leagues = db.query(League).filter(League.is_active.is_(True)).order_by(League.name).all()
    result = []
    for league in leagues:
        matches = db.query(Match).filter(Match.league_id == league.id).all()
        team_ids = {team_id for match in matches for team_id in (match.home_team_id, match.away_team_id)}
        result.append({
            "id": league.id,
            "provider_id": league.provider_id,
            "code": league.provider_code,
            "name": league.name,
            "country": league.country or COMPETITION_AREAS.get(league.provider_code, "International"),
            "emblem_url": league.emblem_url,
            "current_season": league.current_season,
            "team_count": len(team_ids),
            "match_count": len(matches),
        })
    return result
