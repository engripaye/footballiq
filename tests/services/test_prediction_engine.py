import math

import pytest

from app.services.prediction_engine import PredictionEngine


def test_poisson_probability_matches_known_value():
    result = PredictionEngine.poisson_probability(2.0, 2)
    assert result == pytest.approx(2 * math.exp(-2), rel=1e-8)


@pytest.mark.parametrize("home_xg,away_xg", [(2.13, 0.94), (1.1, 1.1), (0.5, 2.4)])
def test_result_probabilities_are_normalized(home_xg, away_xg):
    result = PredictionEngine.calculate_match_result_probabilities(home_xg, away_xg)
    assert sum(result.values()) == pytest.approx(100, abs=0.02)
    assert all(0 <= value <= 100 for value in result.values())


def test_stronger_home_team_is_favoured():
    result = PredictionEngine.calculate_match_result_probabilities(2.13, 0.94)
    assert result["home"] > result["draw"] > result["away"]


def test_low_score_correction_keeps_probabilities_normalized():
    result = PredictionEngine.calculate_match_result_probabilities(0.72, 0.64)
    assert sum(result.values()) == pytest.approx(100, abs=0.02)
    assert result["draw"] > 30


def test_predict_match_returns_explainable_result(db_session, match_data):
    result = PredictionEngine.predict_match(db_session, match_data["match"].id)
    total = result["home_win_probability"] + result["draw_probability"] + result["away_win_probability"]
    assert total == pytest.approx(100, abs=0.02)
    assert 0.2 <= result["expected_home_goals"] <= 4.0
    assert 0.2 <= result["expected_away_goals"] <= 4.0
    assert result["confidence_score"] == max(
        result["home_win_probability"], result["draw_probability"], result["away_win_probability"]
    )
    assert result["risk_level"] in {"low", "medium", "high"}
    assert len(result["reasoning"]) >= 2


def test_predict_match_rejects_unknown_match(db_session):
    with pytest.raises(ValueError, match="Match not found"):
        PredictionEngine.predict_match(db_session, 9999)
