from datetime import date as Date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, aliased

from app.core.database import get_db
from app.core.config import settings
from app.models.league import League
from app.models.match import Match
from app.models.team import Team
from app.services.prediction_engine import PredictionEngine

router = APIRouter(prefix="/fixtures", tags=["Fixtures"])


@router.get("/")
def get_fixtures(
    league_code: str | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=30),
    include_model: bool = Query(default=False),
    date_on: Date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    home_team, away_team = aliased(Team), aliased(Team)
    if date_on:
        local_zone = ZoneInfo(settings.DEFAULT_TIMEZONE)
        start = datetime.combine(date_on, time.min, tzinfo=local_zone).astimezone(timezone.utc)
        end = datetime.combine(date_on + timedelta(days=1), time.min, tzinfo=local_zone).astimezone(timezone.utc)
    else:
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=days)
    if db.bind and db.bind.dialect.name == "sqlite":
        start = start.replace(tzinfo=None)
        end = end.replace(tzinfo=None)
    query = (
        db.query(Match, League, home_team, away_team)
        .join(League, League.id == Match.league_id)
        .join(home_team, home_team.id == Match.home_team_id)
        .join(away_team, away_team.id == Match.away_team_id)
        .filter(Match.status.in_(["SCHEDULED", "TIMED"]))
        .filter(Match.kickoff_time >= start, Match.kickoff_time < end)
        .order_by(Match.kickoff_time.asc())
    )
    if league_code:
        query = query.filter(League.provider_code == league_code.upper())
    fixtures = []
    for match, league, home, away in query.all():
        item = {
            "id": match.id, "provider_id": match.provider_id,
            "league": {"id": league.id, "name": league.name, "code": league.provider_code, "country": league.country, "emblem_url": league.emblem_url},
            "home_team": {"id": home.id, "name": home.name, "short_name": home.short_name, "abbreviation": home.abbreviation, "crest_url": home.crest_url, "country": home.country, "form_score": home.form_score},
            "away_team": {"id": away.id, "name": away.name, "short_name": away.short_name, "abbreviation": away.abbreviation, "crest_url": away.crest_url, "country": away.country, "form_score": away.form_score},
            "kickoff_time": match.kickoff_time, "status": match.status, "season": match.season,
            "matchday": match.matchday, "stage": match.stage, "venue": match.venue,
        }
        if include_model and not (home.name.startswith("TBD (") or away.name.startswith("TBD (")):
            prediction = PredictionEngine.predict_match(db, match.id)
            item["model_prices"] = {
                "home": round(100 / prediction["home_win_probability"], 2),
                "draw": round(100 / prediction["draw_probability"], 2),
                "away": round(100 / prediction["away_win_probability"], 2),
                "label": "FootballiQ fair odds",
            }
        else:
            item["model_prices"] = None
        if include_model and item["model_prices"] is None:
            continue
        fixtures.append(item)
    return fixtures
