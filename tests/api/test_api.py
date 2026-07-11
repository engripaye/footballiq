def test_root_and_health(client):
    root = client.get("/")
    health = client.get("/health")
    assert root.status_code == 200
    assert root.json()["status"] == "running"
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_create_and_list_teams(client):
    payload = {
        "name": "Liverpool",
        "country": "England",
        "league": "Premier League",
        "elo_rating": 1810,
        "attacking_strength": 1.4,
        "defense_strength": 1.1,
        "form_score": 78,
    }
    created = client.post("/api/v1/teams/", json=payload)
    assert created.status_code == 200
    assert created.json()["name"] == "Liverpool"
    listed = client.get("/api/v1/teams/")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_team_validation_rejects_incomplete_payload(client):
    response = client.post("/api/v1/teams/", json={"name": "Incomplete"})
    assert response.status_code == 422


def test_match_detail_endpoint(client, match_data):
    response = client.get(f"/api/v1/matches/{match_data['match'].id}")
    assert response.status_code == 200
    assert response.json()["home_team"]["name"] == "Arsenal"
    assert response.json()["away_team"]["name"] == "Chelsea"


def test_prediction_endpoint(client, match_data):
    response = client.get(f"/api/v1/predictions/{match_data['match'].id}")
    assert response.status_code == 200
    assert response.json()["reasoning"]


def test_intelligence_endpoint(client, match_data):
    response = client.get(f"/api/v1/intelligence/{match_data['match'].id}")
    assert response.status_code == 200
    body = response.json()
    assert body["simulation"]["runs"] == 100_000
    assert body["transparency"]["model_version"] if "model_version" in body["transparency"] else body["model_version"]


def test_unknown_resources_return_404(client):
    assert client.get("/api/v1/matches/9999").status_code == 404
    assert client.get("/api/v1/predictions/9999").status_code == 404
    assert client.get("/api/v1/intelligence/9999").status_code == 404


def test_match_list_pagination_validation(client):
    assert client.get("/api/v1/matches/?limit=0").status_code == 422
    assert client.get("/api/v1/matches/?limit=201").status_code == 422
    assert client.get("/api/v1/matches/?offset=-1").status_code == 422


def test_provider_status_does_not_expose_api_key(client):
    response = client.get("/api/v1/sync/status")
    assert response.status_code == 200
    assert response.json()["provider"] == "football-data.org"
    assert "api_key" not in response.json()
    assert len(response.json()["free_tier_competitions"]) == 12
    assert "WC" in response.json()["free_tier_competitions"]
