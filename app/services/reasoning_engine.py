class ReasoningEngine:

    @staticmethod
    def generate_reasoning(
        home_team,
        away_team,
        home_probability,
        draw_probability,
        away_probability,
        home_injury_impact,
        away_injury_impact,
        expected_home_goals,
        expected_away_goals,
        market_probabilities=None
    ):
        reasoning = []

        if home_team.elo_rating > away_team.elo_rating:
            reasoning.append(
                f"{home_team.name} has a stronger Elo rating than {away_team.name}, which increases their win probability."
            )
        elif away_team.elo_rating > home_team.elo_rating:
            reasoning.append(
                f"{away_team.name} has a stronger Elo rating than {home_team.name}, making the away side competitive."
            )

        if home_team.form_score > away_team.form_score:
            reasoning.append(
                f"{home_team.name} is currently in better form with a form score of {home_team.form_score}."
            )
        elif away_team.form_score > home_team.form_score:
            reasoning.append(
                f"{away_team.name} has better recent form with a form score of {away_team.form_score}."
            )

        if home_injury_impact > 0:
            reasoning.append(
                f"{home_team.name} has active injury concerns reducing their strength by approximately {home_injury_impact}%."
            )

        if away_injury_impact > 0:
            reasoning.append(
                f"{away_team.name} has active injury concerns reducing their strength by approximately {away_injury_impact}%."
            )

        if expected_home_goals > expected_away_goals:
            reasoning.append(
                f"The expected goals model favors {home_team.name} with {expected_home_goals} xG compared to {expected_away_goals} xG."
            )
        elif expected_away_goals > expected_home_goals:
            reasoning.append(
                f"The expected goals model favors {away_team.name} with {expected_away_goals} xG compared to {expected_home_goals} xG."
            )

        if market_probabilities:
            reasoning.append(
                f"Market odds suggest probabilities of Home {market_probabilities['home']}%, Draw {market_probabilities['draw']}%, Away {market_probabilities['away']}%."
            )

        reasoning.append(
            f"Final prediction probabilities are Home {home_probability}%, Draw {draw_probability}%, Away {away_probability}%."
        )

        return reasoning