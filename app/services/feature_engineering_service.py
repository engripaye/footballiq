from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.match import Match


class FeatureEngineeringService:
    """Build pre-match features using only results known before kickoff."""

    @staticmethod
    def build(db: Session, match: Match) -> dict | None:
        completed = (
            db.query(Match)
            .filter(
                Match.league_id == match.league_id,
                Match.kickoff_time < match.kickoff_time,
                Match.home_goals.is_not(None),
                Match.away_goals.is_not(None),
            )
            .order_by(Match.kickoff_time.asc())
            .all()
        )
        if len(completed) < 10:
            return None

        league_home = sum(row.home_goals for row in completed) / len(completed)
        league_away = sum(row.away_goals for row in completed) / len(completed)
        league_home = max(league_home, 0.5)
        league_away = max(league_away, 0.5)

        def venue_stats(team_id: int, home: bool) -> tuple[int, float, float]:
            rows = [row for row in completed if (row.home_team_id if home else row.away_team_id) == team_id]
            if not rows:
                return 0, 1.0, 1.0
            scored = sum(row.home_goals if home else row.away_goals for row in rows) / len(rows)
            conceded = sum(row.away_goals if home else row.home_goals for row in rows) / len(rows)
            attack_base = league_home if home else league_away
            conceded_base = league_away if home else league_home
            weight = len(rows) / (len(rows) + 5)
            return len(rows), 1 + (scored / attack_base - 1) * weight, 1 + (conceded / conceded_base - 1) * weight

        home_n, home_attack, home_defense = venue_stats(match.home_team_id, True)
        away_n, away_attack, away_defense = venue_stats(match.away_team_id, False)

        ratings: dict[int, float] = {}
        for row in completed:
            home_rating = ratings.get(row.home_team_id, 1500.0)
            away_rating = ratings.get(row.away_team_id, 1500.0)
            expected = 1 / (1 + 10 ** ((away_rating - home_rating - 70) / 400))
            actual = 1.0 if row.home_goals > row.away_goals else 0.5 if row.home_goals == row.away_goals else 0.0
            change = 20 * (actual - expected)
            ratings[row.home_team_id] = home_rating + change
            ratings[row.away_team_id] = away_rating - change

        def recent_form(team_id: int) -> tuple[int, float]:
            rows = [row for row in completed if team_id in (row.home_team_id, row.away_team_id)][-8:]
            points = 0
            for row in rows:
                goals_for = row.home_goals if row.home_team_id == team_id else row.away_goals
                goals_against = row.away_goals if row.home_team_id == team_id else row.home_goals
                points += 3 if goals_for > goals_against else 1 if goals_for == goals_against else 0
            return len(rows), (points / (len(rows) * 3)) if rows else 0.5

        home_recent_n, home_form = recent_form(match.home_team_id)
        away_recent_n, away_form = recent_form(match.away_team_id)
        elo_diff = ratings.get(match.home_team_id, 1500) - ratings.get(match.away_team_id, 1500)
        elo_factor = max(0.82, min(1.18, 10 ** (elo_diff / 1600)))
        form_factor = max(0.88, min(1.12, 1 + (home_form - away_form) * 0.18))

        return {
            "expected_home_goals": max(0.2, min(4.0, league_home * home_attack * away_defense * elo_factor * form_factor)),
            "expected_away_goals": max(0.2, min(4.0, league_away * away_attack * home_defense / elo_factor / form_factor)),
            "home_elo": round(ratings.get(match.home_team_id, 1500)),
            "away_elo": round(ratings.get(match.away_team_id, 1500)),
            "home_form": round(home_form * 100),
            "away_form": round(away_form * 100),
            "home_venue_matches": home_n,
            "away_venue_matches": away_n,
            "home_recent_matches": home_recent_n,
            "away_recent_matches": away_recent_n,
            "league_matches": len(completed),
        }
