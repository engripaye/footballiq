from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.odds import Odds
from app.models.team import Team


DEMO_TEAMS = [
    ("Arsenal", "England", "Premier League", 1842, 1.48, 1.14, 82),
    ("Chelsea", "England", "Premier League", 1768, 1.22, 1.08, 67),
    ("Barcelona", "Spain", "LaLiga", 1874, 1.54, 1.18, 86),
    ("Inter Milan", "Italy", "Serie A", 1851, 1.42, 1.21, 79),
    ("Bayern Munich", "Germany", "Bundesliga", 1880, 1.58, 1.12, 84),
    ("Paris Saint-Germain", "France", "Ligue 1", 1862, 1.51, 1.09, 81),
]


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(Team).count():
            return
        teams = [Team(name=n, country=c, league=l, elo_rating=e, attacking_strength=a,
                      defense_strength=d, form_score=f) for n, c, l, e, a, d, f in DEMO_TEAMS]
        db.add_all(teams)
        db.flush()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        pairings = [(0, 1, "Premier League"), (2, 3, "Club World Cup"), (4, 5, "Champions League")]
        for index, (home, away, league) in enumerate(pairings):
            match = Match(home_team_id=teams[home].id, away_team_id=teams[away].id,
                          league=league, season="2026/27", kickoff_time=now + timedelta(hours=8 + index * 20))
            db.add(match)
            db.flush()
            db.add_all([
                Odds(match_id=match.id, bookmaker="NorthStar", home_win_odds=1.72 + index * .18, draw_odds=3.65, away_win_odds=4.8 - index * .3),
                Odds(match_id=match.id, bookmaker="PrimeBet", home_win_odds=1.76 + index * .18, draw_odds=3.55, away_win_odds=4.65 - index * .3),
            ])
        db.commit()
    finally:
        db.close()
