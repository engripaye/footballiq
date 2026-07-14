import pytest

from app.services.intelligence_engine import IntelligenceEngine


def test_intelligence_report_contains_every_core_module(db_session, match_data):
    report = IntelligenceEngine.build_report(db_session, match_data["match"].id)
    required = {
        "prediction", "confidence", "simulation", "goals_markets",
        "tactics", "injuries", "momentum", "odds", "model_markets",
        "conservative_lean", "transparency",
    }
    assert required.issubset(report)
    assert report["model_version"]


def test_simulation_always_totals_one_hundred_thousand(db_session, match_data):
    simulation = IntelligenceEngine.build_report(db_session, match_data["match"].id)["simulation"]
    total = simulation["home_wins"] + simulation["draws"] + simulation["away_wins"]
    assert simulation["runs"] == 100_000
    assert total == 100_000
    assert len(simulation["most_common_scores"]) == 5


def test_confidence_and_market_percentages_are_valid(db_session, match_data):
    report = IntelligenceEngine.build_report(db_session, match_data["match"].id)
    assert 0 <= report["confidence"]["reliability"] <= 100
    assert 0 <= report["goals_markets"]["btts"] <= 100
    assert 0 <= report["goals_markets"]["over_2_5"] <= 100
    assert 0 <= report["goals_markets"]["corners_over_8_5"] <= 100
    assert all(item["fair_odds"] > 1 for item in report["model_markets"])
    assert 0 <= report["confidence"]["outcome_separation"] <= 100


def test_conservative_lean_is_thresholded_and_explained(db_session, match_data):
    report = IntelligenceEngine.build_report(db_session, match_data["match"].id)
    lean = report["conservative_lean"]
    assert lean["reasons"]
    assert "guarantee" in lean["reasons"][-1].lower()
    if lean["probability"] is not None:
        assert lean["probability"] >= 70
        assert lean["fair_odds"] == pytest.approx(100 / lean["probability"], abs=0.01)


def test_score_matrix_is_sorted_and_normalized():
    matrix = IntelligenceEngine._score_matrix(2.1, 0.9)
    assert matrix[0]["probability"] >= matrix[1]["probability"]
    assert sum(row["probability"] for row in matrix) == pytest.approx(100, abs=0.2)


def test_intelligence_rejects_unknown_match(db_session):
    with pytest.raises(ValueError, match="Match not found"):
        IntelligenceEngine.build_report(db_session, 9999)
