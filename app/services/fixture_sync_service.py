from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.league import League
from app.models.match import Match
from app.models.team import Team
from app.providers.base import FootballDataProvider

COMPETITION_AREAS = {
    "PL": "England", "ELC": "England", "PD": "Spain", "BL1": "Germany",
    "SA": "Italy", "FL1": "France", "DED": "Netherlands", "PPL": "Portugal",
    "BSA": "Brazil", "CL": "Europe", "EC": "Europe", "WC": "World",
}


class FixtureSyncService:
    def __init__(self, db: Session, provider: FootballDataProvider) -> None:
        self.db = db
        self.provider = provider

    def sync_competition(self, competition_code: str, date_from: date | None = None, date_to: date | None = None) -> dict[str, int]:
        rows = self.provider.get_matches(competition_code, date_from, date_to)
        counts = {"received": len(rows), "created_teams": 0, "created_matches": 0, "updated_matches": 0}
        for row in rows:
            league = self._upsert_league(row.get("competition") or {}, row.get("season") or {})
            home, home_created = self._upsert_team(row["homeTeam"], league, fallback_provider_id=-(row["id"] * 2))
            away, away_created = self._upsert_team(row["awayTeam"], league, fallback_provider_id=-(row["id"] * 2 + 1))
            counts["created_teams"] += int(home_created) + int(away_created)
            created = self._upsert_match(row, league, home, away)
            counts["created_matches" if created else "updated_matches"] += 1
        self.db.commit()
        return counts

    def _upsert_league(self, data: dict[str, Any], season: dict[str, Any]) -> League:
        league = self.db.query(League).filter(League.provider_id == data["id"]).first()
        if league is None:
            league = League(provider_id=data["id"], name=data.get("name", "Unknown competition"))
            self.db.add(league)
        area = data.get("area") or {}
        league.provider_code, league.name = data.get("code"), data.get("name", "Unknown competition")
        league.country = area.get("name") or COMPETITION_AREAS.get(league.provider_code)
        league.emblem_url = data.get("emblem")
        league.current_season = self._season_label(season)
        self.db.flush()
        return league

    def _upsert_team(self, data: dict[str, Any], league: League, fallback_provider_id: int) -> tuple[Team, bool]:
        provider_id = data.get("id") if data.get("id") is not None else fallback_provider_id
        name = data.get("name") or f"TBD ({abs(fallback_provider_id)})"
        team = self.db.query(Team).filter(Team.provider_id == provider_id).first()
        created = team is None
        if team is None:
            team = Team(provider_id=provider_id, name=name, country=league.country or "Unknown", league=league.name)
            self.db.add(team)
        team.league_id, team.league = league.id, league.name
        team.name, team.short_name = name, data.get("shortName")
        team.abbreviation, team.crest_url = data.get("tla"), data.get("crest")
        team.country = name if league.provider_code in {"WC", "EC"} and not name.startswith("TBD (") else (league.country or team.country or "Unknown")
        self.db.flush()
        return team, created

    def _upsert_match(self, data: dict[str, Any], league: League, home: Team, away: Team) -> bool:
        match = self.db.query(Match).filter(Match.provider_id == data["id"]).first()
        created = match is None
        if match is None:
            match = Match(provider_id=data["id"], home_team_id=home.id, away_team_id=away.id, league=league.name, season=self._season_label(data.get("season") or {}) or "Unknown", kickoff_time=self._parse_datetime(data["utcDate"]))
            self.db.add(match)
        score, referees = data.get("score") or {}, data.get("referees") or []
        full_time, half_time = score.get("fullTime") or {}, score.get("halfTime") or {}
        match.league_id, match.league, match.home_team_id, match.away_team_id = league.id, league.name, home.id, away.id
        match.season, match.kickoff_time = self._season_label(data.get("season") or {}) or "Unknown", self._parse_datetime(data["utcDate"])
        match.matchday, match.stage, match.group_name = data.get("matchday"), data.get("stage"), data.get("group")
        match.status = data.get("status", "SCHEDULED")
        match.home_goals, match.away_goals = full_time.get("home"), full_time.get("away")
        match.half_time_home_goals, match.half_time_away_goals = half_time.get("home"), half_time.get("away")
        match.venue, match.referee = data.get("venue"), referees[0].get("name") if referees else None
        self.db.flush()
        return created

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _season_label(data: dict[str, Any]) -> str | None:
        start, end = data.get("startDate"), data.get("endDate")
        return None if not start else (start[:4] if not end else f"{start[:4]}/{end[:4]}")
