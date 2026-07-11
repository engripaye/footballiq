import os

# This must happen before application imports so tests never touch PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite:///./test_bootstrap.db"
os.environ["SEED_DEMO_DATA"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.injury  # noqa: F401
import app.models.match  # noqa: F401
import app.models.league  # noqa: F401
import app.models.odds  # noqa: F401
import app.models.player  # noqa: F401
import app.models.prediction  # noqa: F401
import app.models.team  # noqa: F401
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def match_data(db_session):
    from datetime import datetime, timedelta
    from app.models.match import Match
    from app.models.odds import Odds
    from app.models.team import Team

    home = Team(
        name="Arsenal", country="England", league="Premier League",
        elo_rating=1842, attacking_strength=1.48,
        defense_strength=1.14, form_score=82,
    )
    away = Team(
        name="Chelsea", country="England", league="Premier League",
        elo_rating=1768, attacking_strength=1.22,
        defense_strength=1.08, form_score=67,
    )
    db_session.add_all([home, away])
    db_session.flush()

    match = Match(
        home_team_id=home.id,
        away_team_id=away.id,
        league="Premier League",
        season="2026/27",
        kickoff_time=datetime.utcnow() + timedelta(days=1),
    )
    db_session.add(match)
    db_session.flush()
    db_session.add_all([
        Odds(match_id=match.id, bookmaker="NorthStar", home_win_odds=1.72,
             draw_odds=3.65, away_win_odds=4.80),
        Odds(match_id=match.id, bookmaker="PrimeBet", home_win_odds=1.76,
             draw_odds=3.55, away_win_odds=4.65),
    ])
    db_session.commit()
    return {"match": match, "home": home, "away": away}
