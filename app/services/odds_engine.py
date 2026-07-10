from sqlalchemy.orm import Session
from app.models.odds import Odds


class OddsEngine:

    @staticmethod
    def get_average_market_probability(db: Session, match_id: int):
        odds = db.query(Odds).filter(Odds.match_id == match_id).all()

        if not odds:
            return None

        home_probs = []
        draw_probs = []
        away_probs = []

        for item in odds:
            home_probs.append(1 / item.home_win_odds)
            draw_probs.append(1 / item.draw_odds)
            away_probs.append(1 / item.away_win_odds)

        avg_home = sum(home_probs) / len(home_probs)
        avg_draw = sum(draw_probs) / len(draw_probs)
        avg_away = sum(away_probs) / len(away_probs)

        total = avg_home + avg_draw + avg_away

        return {
            "home": round((avg_home / total) * 100, 2),
            "draw": round((avg_draw / total) * 100, 2),
            "away": round((avg_away / total) * 100, 2),
        }