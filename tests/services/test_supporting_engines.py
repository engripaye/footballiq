import pytest

from app.models.injury import Injury
from app.services.injury_engine import InjuryEngine
from app.services.odds_engine import OddsEngine


def test_odds_engine_removes_margin_and_normalizes(db_session, match_data):
    result = OddsEngine.get_average_market_probability(db_session, match_data["match"].id)
    assert sum(result.values()) == pytest.approx(100, abs=0.02)
    assert result["home"] > result["draw"]
    assert result["home"] > result["away"]


def test_odds_engine_returns_none_without_market(db_session):
    assert OddsEngine.get_average_market_probability(db_session, 999) is None


def test_injury_impact_only_counts_active_injuries(db_session, match_data):
    team_id = match_data["home"].id
    db_session.add_all([
        Injury(player_id=1, team_id=team_id, impact_score=12, is_active=True),
        Injury(player_id=2, team_id=team_id, impact_score=20, is_active=False),
    ])
    db_session.commit()
    assert InjuryEngine.calculate_team_injury_impact(db_session, team_id) == 12


def test_injury_impact_is_capped_at_thirty(db_session, match_data):
    team_id = match_data["home"].id
    db_session.add_all([
        Injury(player_id=1, team_id=team_id, impact_score=20, is_active=True),
        Injury(player_id=2, team_id=team_id, impact_score=20, is_active=True),
    ])
    db_session.commit()
    assert InjuryEngine.calculate_team_injury_impact(db_session, team_id) == 30


def test_team_without_injuries_has_zero_impact(db_session, match_data):
    assert InjuryEngine.calculate_team_injury_impact(db_session, match_data["away"].id) == 0
