from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.league import League
from app.models.match import Match
from app.models.team import Team

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("/")
def get_leagues(db: Session = Depends(get_db)):
    rows = (
        db.query(
            League,
            func.count(func.distinct(Team.id)).label("team_count"),
            func.count(func.distinct(Match.id)).label("match_count"),
        )
        .outerjoin(Team, Team.league_id == League.id)
        .outerjoin(Match, Match.league_id == League.id)
        .group_by(League.id)
        .order_by(League.name)
        .all()
    )
    return [
        {
            "id": league.id,
            "provider_id": league.provider_id,
            "code": league.provider_code,
            "name": league.name,
            "country": league.country,
            "emblem_url": league.emblem_url,
            "current_season": league.current_season,
            "team_count": team_count,
            "match_count": match_count,
        }
        for league, team_count, match_count in rows
    ]
