from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class FootballDataProvider(ABC):
    @abstractmethod
    def get_competitions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_matches(self, competition_code: str, date_from: date | None = None, date_to: date | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_team(self, team_id: int) -> dict[str, Any]:
        raise NotImplementedError
