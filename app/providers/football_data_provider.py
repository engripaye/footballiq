from datetime import date
import time
from typing import Any

import httpx

from app.core.config import settings
from app.providers.base import FootballDataProvider


class FootballDataOrgProvider(FootballDataProvider):
    def __init__(self) -> None:
        if not settings.FOOTBALL_DATA_API_KEY:
            raise ValueError("FOOTBALL_DATA_API_KEY is not configured")
        self.client = httpx.Client(
            base_url=settings.FOOTBALL_DATA_BASE_URL.rstrip("/"), timeout=30.0,
            headers={"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY, "Accept": "application/json"},
        )

    def close(self) -> None:
        self.client.close()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(3):
            try:
                response = self.client.get(endpoint, params=params)
                if response.status_code == 429:
                    raise RuntimeError("Football data provider rate limit reached")
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError("Unexpected football provider response")
                return payload
            except (httpx.TransportError, RuntimeError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Football data provider request failed")

    def get_competitions(self) -> list[dict[str, Any]]:
        return self._get("/competitions").get("competitions", [])

    def get_matches(self, competition_code: str, date_from: date | None = None, date_to: date | None = None) -> list[dict[str, Any]]:
        params = {}
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        return self._get(f"/competitions/{competition_code}/matches", params=params).get("matches", [])

    def get_team(self, team_id: int) -> dict[str, Any]:
        return self._get(f"/teams/{team_id}")
