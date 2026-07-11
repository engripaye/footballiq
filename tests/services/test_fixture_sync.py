from datetime import datetime, timedelta, timezone

from app.models.league import League
from app.services.fixture_sync_service import FixtureSyncService


class FakeProvider:
    def get_matches(self, competition_code, date_from=None, date_to=None):
        return [{
            "id": 99, "utcDate": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "status": "SCHEDULED",
            "competition": {"id": 2021, "code": competition_code, "name": "Premier League", "area": {"name": "England"}},
            "season": {"startDate": "2026-08-01", "endDate": "2027-05-31"},
            "homeTeam": {"id": 1, "name": "Arsenal", "shortName": "Arsenal", "tla": "ARS"},
            "awayTeam": {"id": 2, "name": "Chelsea", "shortName": "Chelsea", "tla": "CHE"},
            "score": {"fullTime": {"home": None, "away": None}}, "referees": [],
        }]


def test_fixture_sync_is_idempotent(db_session):
    service = FixtureSyncService(db_session, FakeProvider())
    first = service.sync_competition("PL")
    second = service.sync_competition("PL")
    assert first["created_matches"] == 1
    assert second["updated_matches"] == 1
    assert db_session.query(League).one().provider_code == "PL"


def test_fixture_endpoint_returns_synced_matches(client, db_session):
    FixtureSyncService(db_session, FakeProvider()).sync_competition("PL")
    response = client.get("/api/v1/fixtures/?league_code=pl&days=7")
    assert response.status_code == 200
    assert response.json()[0]["home_team"]["name"] == "Arsenal"


def test_sync_validates_dates_before_provider_configuration(client):
    response = client.post("/api/v1/sync/competitions/PL?date_from=2026-08-02&date_to=2026-08-01")
    assert response.status_code == 400
