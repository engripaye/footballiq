from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match import Match
from app.models.team import Team
from app.providers.football_data_provider import FootballDataOrgProvider
from app.services.lineup_service import LineupService

router = APIRouter(prefix="/lineups", tags=["Projected lineups"])


@router.get("/{match_id}")
def projected_lineups(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    teams = [db.query(Team).filter(Team.id == team_id).first() for team_id in (match.home_team_id, match.away_team_id)]
    if any(team is None or not team.provider_id or team.provider_id < 0 for team in teams):
        raise HTTPException(status_code=409, detail="Confirmed fixture participants with provider IDs are required")
    provider = FootballDataOrgProvider()
    try:
        projections = [LineupService.project(provider.get_team(team.provider_id)) for team in teams]
        return {"match_id": match_id, "home": projections[0], "away": projections[1]}
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Unable to load registered squads: {error}") from error
    finally:
        provider.close()
