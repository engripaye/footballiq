import math
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.match import Match
from app.services.injury_engine import InjuryEngine
from app.services.odds_engine import OddsEngine
from app.services.reasoning_engine import ReasoningEngine
from app.services.feature_engineering_service import FeatureEngineeringService


class PredictionEngine:

    @staticmethod
    def poisson_probability(lmbda: float, goals: int) -> float:
        return (math.exp(-lmbda) * (lmbda ** goals)) / math.factorial(goals)

    @staticmethod
    def calculate_match_result_probabilities(home_xg: float, away_xg: float):
        """Return normalized 1X2 probabilities using a Dixon-Coles adjustment.

        The low-score correction reduces the independence bias of a plain
        Poisson model around 0-0, 1-0, 0-1 and 1-1. The grid is deliberately
        extended to ten goals so high-scoring tail mass is not discarded.
        """
        home_win = 0
        draw = 0
        away_win = 0
        rho = -0.08

        for home_goals in range(0, 11):
            for away_goals in range(0, 11):
                probability = (
                    PredictionEngine.poisson_probability(home_xg, home_goals)
                    * PredictionEngine.poisson_probability(away_xg, away_goals)
                )
                if home_goals == 0 and away_goals == 0:
                    probability *= 1 - (home_xg * away_xg * rho)
                elif home_goals == 0 and away_goals == 1:
                    probability *= 1 + (home_xg * rho)
                elif home_goals == 1 and away_goals == 0:
                    probability *= 1 + (away_xg * rho)
                elif home_goals == 1 and away_goals == 1:
                    probability *= 1 - rho

                if home_goals > away_goals:
                    home_win += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away_win += probability

        total = home_win + draw + away_win

        return {
            "home": round((home_win / total) * 100, 2),
            "draw": round((draw / total) * 100, 2),
            "away": round((away_win / total) * 100, 2),
        }

    @staticmethod
    def predict_match(db: Session, match_id: int):
        match = db.query(Match).filter(Match.id == match_id).first()

        if not match:
            raise ValueError("Match not found")

        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()

        if not home_team or not away_team:
            raise ValueError("Teams not found")
        if home_team.name.startswith("TBD (") or away_team.name.startswith("TBD ("):
            raise ValueError("Fixture participants are not confirmed yet")

        home_injury_impact = InjuryEngine.calculate_team_injury_impact(
            db=db,
            team_id=home_team.id
        )

        away_injury_impact = InjuryEngine.calculate_team_injury_impact(
            db=db,
            team_id=away_team.id
        )

        features = FeatureEngineeringService.build(db, match) if match.league_id else None

        # Legacy/demo fallback when there is not enough historical provider data.
        # dampened so an excellent team does not produce unrealistic 4–5 xG forecasts.
        home_strength = (1.35 * (home_team.attacking_strength / max(away_team.defense_strength, .5))
                         * ((home_team.elo_rating / 1500) ** .35) * (.70 + home_team.form_score / 200) * 1.08)
        away_strength = (1.15 * (away_team.attacking_strength / max(home_team.defense_strength, .5))
                         * ((away_team.elo_rating / 1500) ** .35) * (.70 + away_team.form_score / 200))

        home_strength = home_strength * (1 - home_injury_impact / 100)
        away_strength = away_strength * (1 - away_injury_impact / 100)

        expected_home_goals = round(features["expected_home_goals"] if features else min(max(home_strength, 0.2), 4.0), 2)
        expected_away_goals = round(features["expected_away_goals"] if features else min(max(away_strength, 0.2), 4.0), 2)

        model_probabilities = PredictionEngine.calculate_match_result_probabilities(
            home_xg=expected_home_goals,
            away_xg=expected_away_goals
        )

        market_probabilities = OddsEngine.get_average_market_probability(
            db=db,
            match_id=match_id
        )

        if market_probabilities:
            home_probability = round(
                (model_probabilities["home"] * 0.7) + (market_probabilities["home"] * 0.3),
                2
            )
            draw_probability = round(
                (model_probabilities["draw"] * 0.7) + (market_probabilities["draw"] * 0.3),
                2
            )
            away_probability = round(
                (model_probabilities["away"] * 0.7) + (market_probabilities["away"] * 0.3),
                2
            )
        else:
            home_probability = model_probabilities["home"]
            draw_probability = model_probabilities["draw"]
            away_probability = model_probabilities["away"]

        probabilities = [home_probability, draw_probability, away_probability]
        confidence_score = round(max(probabilities), 2)

        if confidence_score >= 75:
            risk_level = "low"
        elif confidence_score >= 60:
            risk_level = "medium"
        else:
            risk_level = "high"

        reasoning = ReasoningEngine.generate_reasoning(
            home_team=home_team,
            away_team=away_team,
            home_probability=home_probability,
            draw_probability=draw_probability,
            away_probability=away_probability,
            home_injury_impact=home_injury_impact,
            away_injury_impact=away_injury_impact,
            expected_home_goals=expected_home_goals,
            expected_away_goals=expected_away_goals,
            market_probabilities=market_probabilities
        )
        if features:
            reasoning = [
                f"Calculated from {features['league_matches']} completed league matches available before kickoff.",
                f"Current sequential Elo: {home_team.name} {features['home_elo']} and {away_team.name} {features['away_elo']} ({abs(features['home_elo'] - features['away_elo'])} points apart).",
                f"Last-eight points rate: {home_team.name} {features['home_form']}% from {features['home_recent_matches']} matches; {away_team.name} {features['away_form']}% from {features['away_recent_matches']}.",
                f"Venue evidence: {home_team.name} average {features['home_goals_for']} scored and {features['home_goals_against']} conceded at home; {away_team.name} average {features['away_goals_for']} scored and {features['away_goals_against']} conceded away.",
                f"Expected-goal projection is {expected_home_goals}–{expected_away_goals}; it blends league scoring rates, opponent defence, Elo and recent form with sample-size shrinkage.",
                f"A Dixon–Coles low-score correction converts that goal projection into {home_probability}% home, {draw_probability}% draw and {away_probability}% away.",
                "No confirmed-lineup, verified injury or weather feed is connected, so these missing inputs reduce report reliability and can change the pre-kickoff view.",
            ]

        return {
            "match_id": match_id,
            "home_win_probability": home_probability,
            "draw_probability": draw_probability,
            "away_win_probability": away_probability,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "expected_home_goals": expected_home_goals,
            "expected_away_goals": expected_away_goals,
            "reasoning": reasoning,
            "data_quality": {
                "source": "football-data.org" if match.provider_id else "local_demo",
                "historical_matches": features["league_matches"] if features else 0,
                "home_venue_matches": features["home_venue_matches"] if features else 0,
                "away_venue_matches": features["away_venue_matches"] if features else 0,
                "home_recent_matches": features["home_recent_matches"] if features else 0,
                "away_recent_matches": features["away_recent_matches"] if features else 0,
                "home_elo": features["home_elo"] if features else round(home_team.elo_rating),
                "away_elo": features["away_elo"] if features else round(away_team.elo_rating),
                "home_form": features["home_form"] if features else round(home_team.form_score),
                "away_form": features["away_form"] if features else round(away_team.form_score),
                "lineups_confirmed": False,
                "injury_data_available": False,
                "historical_model_calibrated": False,
            },
        }
