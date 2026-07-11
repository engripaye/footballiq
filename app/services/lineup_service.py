from typing import Any


class LineupService:
    FORMATION = "4-3-3"
    POSITION_LIMITS = {"Goalkeeper": 1, "Defence": 4, "Midfield": 3, "Offence": 3}

    @classmethod
    def project(cls, team_payload: dict[str, Any]) -> dict[str, Any]:
        squad = team_payload.get("squad") or []
        selected = []
        for position, limit in cls.POSITION_LIMITS.items():
            candidates = [player for player in squad if player.get("position") == position]
            for index, player in enumerate(candidates[:limit]):
                selected.append({
                    "provider_id": player.get("id"),
                    "name": player.get("name", "Unknown player"),
                    "position": position,
                    "slot": cls._slot(position, index),
                })
        return {
            "team": team_payload.get("name", "Unknown team"),
            "crest_url": team_payload.get("crest"),
            "formation": cls.FORMATION,
            "coach": (team_payload.get("coach") or {}).get("name"),
            "players": selected,
            "status": "squad-based projection",
            "confidence": "low",
            "explanation": "Projected from the registered squad by position. It is not a confirmed or provider-predicted starting XI.",
        }

    @staticmethod
    def _slot(position: str, index: int) -> str:
        slots = {
            "Goalkeeper": ["GK"],
            "Defence": ["LB", "LCB", "RCB", "RB"],
            "Midfield": ["LCM", "CM", "RCM"],
            "Offence": ["LW", "ST", "RW"],
        }
        return slots[position][index]
