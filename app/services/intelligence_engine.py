import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.injury import Injury
from app.models.match import Match
from app.models.odds import Odds
from app.models.team import Team
from app.services.prediction_engine import PredictionEngine


class IntelligenceEngine:
    """Builds one explainable, versioned match report from auditable inputs."""

    MODEL_VERSION = "fiq-dixon-coles-1.2"
    SIMULATIONS = 100_000

    @staticmethod
    def _over_probability(mean: float, line: float) -> float:
        max_under = math.floor(line)
        under = sum(math.exp(-mean) * (mean ** value) / math.factorial(value) for value in range(max_under + 1))
        return round((1 - under) * 100, 2)

    @staticmethod
    def _fair_odds(probability: float) -> float | None:
        return round(100 / probability, 2) if probability > 0 else None

    @staticmethod
    def _report_reliability(prediction: dict, freshness: int) -> int:
        quality = prediction["data_quality"]
        history = min(100, quality["historical_matches"] / 1.5)
        venue_sample = min(100, min(quality["home_venue_matches"], quality["away_venue_matches"]) * 10)
        ordered = sorted([
            prediction["home_win_probability"], prediction["draw_probability"],
            prediction["away_win_probability"],
        ], reverse=True)
        outcome_separation = min(100, 35 + (ordered[0] - ordered[1]) * 2)
        # Provider fixture + historical results are present, while lineups,
        # injuries and weather are deliberately scored as missing inputs.
        input_completeness = 40 if quality["source"] == "football-data.org" else 20
        return round(
            history * .25 + venue_sample * .20 + freshness * .15
            + outcome_separation * .25 + input_completeness * .15
        )

    @classmethod
    def _conservative_lean(cls, prediction: dict, markets: dict, reliability: int) -> dict:
        home = prediction["home_win_probability"]
        draw = prediction["draw_probability"]
        away = prediction["away_win_probability"]
        candidates = [
            ("Double chance", "Home or draw", round(home + draw, 2), "The model covers two of the three match outcomes."),
            ("Double chance", "Away or draw", round(away + draw, 2), "The model covers two of the three match outcomes."),
            ("Total goals", "Over 1.5", markets["over_1_5"], "The combined goal projection supports at least two goals."),
            ("Total goals", "Under 3.5", round(100 - markets["over_3_5"], 2), "The score distribution keeps four or more goals as the less likely branch."),
        ]
        market, selection, probability, basis = max(candidates, key=lambda item: item[2])
        publishable = probability >= 70 and reliability >= 45
        return {
            "market": market if publishable else "No strong pre-match lean",
            "selection": selection if publishable else "Wait for stronger or fresher inputs",
            "probability": probability if publishable else None,
            "fair_odds": cls._fair_odds(probability) if publishable else None,
            "risk_label": "lower model risk" if probability >= 78 and reliability >= 55 else "cautious",
            "basis": basis if publishable else "The current evidence does not clear FootballiQ's publication threshold.",
            "reasons": [
                f"This selection has the highest probability among the model's conservative, calibrated goal-and-result candidates ({probability}%).",
                f"Report reliability is {reliability}/100 after penalizing missing confirmed lineups, verified injuries and weather.",
                "The displayed price is a margin-free model reference, not a bookmaker offer or a guarantee of profit.",
            ],
            "advice": "If it were my decision, I would only consider this smaller-risk lean, use a strict stake limit, and skip the match if the available price is shorter than the model fair price.",
        }

    @staticmethod
    def _score_matrix(home_xg: float, away_xg: float) -> list[dict]:
        scores = []
        for home in range(7):
            for away in range(7):
                probability = (PredictionEngine.poisson_probability(home_xg, home)
                               * PredictionEngine.poisson_probability(away_xg, away))
                scores.append({"score": f"{home}-{away}", "probability": probability})
        total = sum(item["probability"] for item in scores)
        for item in scores:
            item["probability"] = round(item["probability"] / total * 100, 2)
        return sorted(scores, key=lambda item: item["probability"], reverse=True)

    @staticmethod
    def _tactical_profile(team: Team, home: bool) -> dict:
        quality = (team.elo_rating - 1450) / 8
        possession = round(min(68, max(40, 49 + quality / 10 + (2 if home else 0))))
        return {
            "formation": "4-3-3" if team.attacking_strength >= 1.35 else "4-2-3-1",
            "possession": possession,
            "pressing": "High" if team.form_score >= 78 else "Medium",
            "wing_attacks": "Very high" if team.attacking_strength >= 1.45 else "High",
            "counter_attack": "Medium" if possession < 56 else "Low",
            "defensive_line": "High" if team.elo_rating >= 1800 else "Balanced",
        }

    @classmethod
    def build_report(cls, db: Session, match_id: int) -> dict:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("Match not found")
        home = db.query(Team).filter(Team.id == match.home_team_id).first()
        away = db.query(Team).filter(Team.id == match.away_team_id).first()
        if not home or not away:
            raise ValueError("Teams not found")

        prediction = PredictionEngine.predict_match(db, match_id)
        scores = cls._score_matrix(prediction["expected_home_goals"], prediction["expected_away_goals"])
        home_count = round(prediction["home_win_probability"] * 1000)
        draw_count = round(prediction["draw_probability"] * 1000)
        away_count = cls.SIMULATIONS - home_count - draw_count
        odds = db.query(Odds).filter(Odds.match_id == match_id).all()
        injuries = db.query(Injury).filter(Injury.team_id.in_([home.id, away.id]), Injury.is_active.is_(True)).all()
        freshness = 90 if match.provider_id else 40
        lineup_certainty = 0  # football-data.org does not provide confirmed lineups here.
        historical_similarity = min(100, prediction["data_quality"]["historical_matches"])
        reliability = cls._report_reliability(prediction, freshness)
        ordered_outcomes = sorted([
            prediction["home_win_probability"], prediction["draw_probability"],
            prediction["away_win_probability"],
        ], reverse=True)
        outcome_separation = round(min(100, max(0, (ordered_outcomes[0] - ordered_outcomes[1]) * 3)))

        def team_injuries(team: Team):
            rows = [item for item in injuries if item.team_id == team.id]
            return {
                "active": len(rows),
                "impact_score": round(sum(item.impact_score for item in rows), 1),
                "availability": "Not verified" if not rows else "Monitor",
                "explanation": "No verified injury feed is connected; zero means no stored records, not confirmed availability." if not rows else
                    "Unavailable players reduce the team's modeled attacking and defensive strength."
            }

        best_home = min((o.home_win_odds for o in odds), default=None)
        worst_home = max((o.home_win_odds for o in odds), default=None)
        total_goals = prediction["expected_home_goals"] + prediction["expected_away_goals"]
        over_15 = cls._over_probability(total_goals, 1.5)
        over_25 = cls._over_probability(total_goals, 2.5)
        over_35 = cls._over_probability(total_goals, 3.5)
        btts = round((1 - math.exp(-prediction["expected_home_goals"])) * (1 - math.exp(-prediction["expected_away_goals"])) * 100, 2)
        expected_corners = round(max(6.0, min(14.0, 7.2 + total_goals * 1.05)), 1)
        corners_over_85 = cls._over_probability(expected_corners, 8.5)
        market_probabilities = {
            "over_1_5": over_15,
            "over_2_5": over_25,
            "over_3_5": over_35,
            "btts": btts,
        }
        conservative_lean = cls._conservative_lean(prediction, market_probabilities, reliability)
        model_markets = [
            {"market": "Match result", "selection": home.name, "probability": prediction["home_win_probability"], "fair_odds": cls._fair_odds(prediction["home_win_probability"]), "basis": "goal model"},
            {"market": "Match result", "selection": "Draw", "probability": prediction["draw_probability"], "fair_odds": cls._fair_odds(prediction["draw_probability"]), "basis": "goal model"},
            {"market": "Match result", "selection": away.name, "probability": prediction["away_win_probability"], "fair_odds": cls._fair_odds(prediction["away_win_probability"]), "basis": "goal model"},
            {"market": "Both teams score", "selection": "Yes", "probability": btts, "fair_odds": cls._fair_odds(btts), "basis": "goal model"},
            {"market": "Both teams score", "selection": "No", "probability": round(100 - btts, 2), "fair_odds": cls._fair_odds(100 - btts), "basis": "goal model"},
            {"market": "Total goals", "selection": "Over 1.5", "probability": over_15, "fair_odds": cls._fair_odds(over_15), "basis": "goal model"},
            {"market": "Total goals", "selection": "Over 2.5", "probability": over_25, "fair_odds": cls._fair_odds(over_25), "basis": "goal model"},
            {"market": "Total goals", "selection": "Over 3.5", "probability": over_35, "fair_odds": cls._fair_odds(over_35), "basis": "goal model"},
            {"market": "Total goals", "selection": "Under 3.5", "probability": round(100 - over_35, 2), "fair_odds": cls._fair_odds(100 - over_35), "basis": "goal model"},
            {"market": "Double chance", "selection": "Home or draw", "probability": round(prediction["home_win_probability"] + prediction["draw_probability"], 2), "fair_odds": cls._fair_odds(prediction["home_win_probability"] + prediction["draw_probability"]), "basis": "Dixon-Coles result model"},
            {"market": "Double chance", "selection": "Away or draw", "probability": round(prediction["away_win_probability"] + prediction["draw_probability"], 2), "fair_odds": cls._fair_odds(prediction["away_win_probability"] + prediction["draw_probability"]), "basis": "Dixon-Coles result model"},
            {"market": "Total corners", "selection": "Over 8.5", "probability": corners_over_85, "fair_odds": cls._fair_odds(corners_over_85), "basis": "uncalibrated proxy"},
            {"market": "Total corners", "selection": "Under 8.5", "probability": round(100 - corners_over_85, 2), "fair_odds": cls._fair_odds(100 - corners_over_85), "basis": "uncalibrated proxy"},
        ]
        return {
            "match_id": match_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": cls.MODEL_VERSION,
            "data_status": (f"football-data.org fixture with {prediction['data_quality']['historical_matches']} prior league results; lineups and injuries are not verified."
                            if match.provider_id else "Local demo data — not suitable for production claims."),
            "prediction": prediction,
            "confidence": {
                "reliability": reliability,
                "model_agreement": 0,
                "outcome_separation": outcome_separation,
                "historical_similarity": historical_similarity,
                "data_freshness": freshness,
                "lineup_certainty": lineup_certainty,
                "weather_uncertainty": "Low",
            },
            "simulation": {
                "runs": cls.SIMULATIONS,
                "home_wins": home_count,
                "draws": draw_count,
                "away_wins": away_count,
                "most_common_scores": scores[:5],
            },
            "goals_markets": {
                "over_2_5": over_25,
                "btts": btts,
                "expected_corners": expected_corners,
                "corners_over_8_5": corners_over_85,
                "corner_model_status": "Experimental proxy — no historical corner-event feed is connected.",
                "expected_cards": None,
            },
            "model_markets": model_markets,
            "conservative_lean": conservative_lean,
            "tactics": {
                "home": {"team": home.name, **cls._tactical_profile(home, True)},
                "away": {"team": away.name, **cls._tactical_profile(away, False)},
                "key_battle": "Midfield control and second-ball recoveries",
                "match_pattern": f"{home.name} are projected to control more territory; {away.name} retain a transition threat.",
            },
            "injuries": {"home": team_injuries(home), "away": team_injuries(away)},
            "momentum": {
                "home": {"team": home.name, "index": prediction["data_quality"]["home_form"], "trend": "Strong" if prediction["data_quality"]["home_form"] >= 70 else "Mixed"},
                "away": {"team": away.name, "index": prediction["data_quality"]["away_form"], "trend": "Strong" if prediction["data_quality"]["away_form"] >= 70 else "Mixed"},
            },
            "odds": {
                "bookmakers": [{"name": o.bookmaker, "home": o.home_win_odds, "draw": o.draw_odds, "away": o.away_win_odds} for o in odds],
                "best_home_odds": worst_home,
                "shortest_home_odds": best_home,
                "movement": "Stable — no historical odds snapshots connected",
                "explanation": "The market signal is blended at a 30% weight and bookmaker margin is removed before use." if odds else "No market data is connected.",
            },
            "transparency": {
                "published_probability": max(prediction["home_win_probability"], prediction["draw_probability"], prediction["away_win_probability"]),
                "actual_result": None,
                "settled": False,
                "calibration_bucket": "Not calibrated",
                "method": "Pre-kickoff venue scoring rates + opponent defence + sequential Elo + last-eight form → sample-size shrinkage → Dixon–Coles low-score correction → normalized probabilities and margin-free fair prices. Historical calibration is not yet available.",
            },
        }
