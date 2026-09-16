from conftest import login


def test_permission_contract_and_management_data_gate(client):
    login(client, "maya@atplcrm.local")
    permissions = client.get("/api/v1/permissions/")
    assert permissions.status_code == 200
    granted = {row["code"] for row in permissions.json()["capabilities"] if row["granted"]}
    assert "search.use" in granted
    assert "data.manage" not in granted
    assert client.get("/api/v1/data/imports/").status_code == 403
    assert client.get("/api/v1/data/duplicates/").status_code == 403
    assert client.get("/api/v1/data/quality/").status_code == 403


def test_ranked_search_recent_history_and_pagination(client):
    csrf = login(client)
    result = client.get("/api/v1/data/search/?q=Northstar&page=1&page_size=2")
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["total"] >= 1
    assert payload["page"] == 1 and payload["page_size"] == 2
    assert payload["results"][0]["rank"] > 0

    remembered = client.post(
        "/api/v1/data/search/recent/",
        json={"query": "Northstar", "entity_type": "all", "country": ""},
        headers={"X-CSRFToken": csrf},
    )
    assert remembered.status_code == 201, remembered.text
    history = client.get("/api/v1/data/search/recent/").json()
    assert history[0]["query"] == "Northstar"
    assert client.delete("/api/v1/data/search/recent/", headers={"X-CSRFToken": csrf}).status_code == 200
    assert client.get("/api/v1/data/search/recent/").json() == []


def test_local_login_throttle(client):
    csrf = client.get("/api/v1/session/").json()["csrf"]
    for _ in range(5):
        response = client.post(
            "/api/v1/session/",
            json={"username": "throttle-check@invalid.local", "password": "wrong-password"},
            headers={"X-CSRFToken": csrf},
        )
        assert response.status_code == 400
    blocked = client.post(
        "/api/v1/session/",
        json={"username": "throttle-check@invalid.local", "password": "wrong-password"},
        headers={"X-CSRFToken": csrf},
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_bootstrap_exposes_bounded_working_set(client):
    login(client)
    payload = client.get("/api/v1/bootstrap/").json()
    loaded_pursuits = {row["id"] for row in payload["leads"] + payload["opportunities"]}
    assert payload["workspace_counts"]["pursuits"] >= len(loaded_pursuits)
    assert payload["working_set"]["pursuits"] == len(loaded_pursuits)
    assert payload["working_set"]["pursuits"] <= 100
