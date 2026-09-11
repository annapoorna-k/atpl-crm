from datetime import date, timedelta

from conftest import login


def test_health_and_authentication_boundary(client):
    assert client.get("/api/health/").json()["framework"] == "FastAPI"
    assert client.get("/api/v1/bootstrap/").status_code == 403
    csrf = client.get("/api/v1/session/").json()["csrf"]
    denied = client.post(
        "/api/v1/session/",
        json={"username": "alex@atplcrm.local", "password": "wrong"},
        headers={"X-CSRFToken": csrf},
    )
    assert denied.status_code == 400


def test_bootstrap_has_complete_workspace_contract(client):
    login(client)
    response = client.get("/api/v1/bootstrap/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["instance"] == "INTERNATIONAL"
    assert data["user"]["level"] == "Manager"
    assert data["companies"] and data["contacts"] and data["leads"]
    assert data["opportunities"] and data["reference"]["stages"]
    assert data["opportunities"][0]["values_visible"] is True


def test_csrf_and_validation_are_enforced(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    response = client.post(
        "/api/v1/companies/",
        json={"name": "No CSRF", "country": "India", "owner": data["user"]["id"]},
    )
    assert response.status_code == 403
    invalid = client.post(
        "/api/v1/companies/",
        json={"name": "", "country": "", "owner": data["user"]["id"]},
        headers={"X-CSRFToken": csrf},
    )
    assert invalid.status_code == 422
    assert "name" in invalid.json()


def test_create_lead_and_reject_past_action(client):
    csrf = login(client, "maya@atplcrm.local")
    data = client.get("/api/v1/bootstrap/").json()
    payload = {
        "name": "Regional analytics rollout",
        "company": data["companies"][0]["id"],
        "owner": data["user"]["id"],
        "holder": data["user"]["id"],
        "next_action": "Call the sponsor",
        "action_type": "Call",
        "action_date": str(date.today() + timedelta(days=2)),
        "source_channel": "LinkedIn",
        "source_detail": "Direct outreach",
        "priority": "High",
        "area_of_interest": "Analytics",
    }
    created = client.post("/api/v1/leads/", json=payload, headers={"X-CSRFToken": csrf})
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "new"
    payload["name"] = "Invalid dated lead"
    payload["action_date"] = str(date.today())
    invalid = client.post("/api/v1/leads/", json=payload, headers={"X-CSRFToken": csrf})
    assert invalid.status_code == 422


def test_standard_user_cannot_self_validate_a_ready_lead(client):
    csrf = login(client, "maya@atplcrm.local")
    data = client.get("/api/v1/bootstrap/").json()
    lead = next(item for item in data["leads"] if item["status"] == "working")
    ready = client.post(
        f'/api/v1/leads/{lead["lead_id"]}/status/',
        json={"status": "ready"},
        headers={"X-CSRFToken": csrf},
    )
    assert ready.status_code == 200, ready.text
    convert = client.post(
        f'/api/v1/leads/{lead["lead_id"]}/convert/',
        json={
            "customer_need": "Establish a governed AI roadmap",
            "scope_summary": "Assessment and prioritized plan",
            "primary_contact": data["contacts"][0]["id"],
            "current_value": "25000",
            "currency": "USD",
                "service_line": data["reference"]["services"][0][0],
            "expected_close_date": str(date.today() + timedelta(days=30)),
        },
        headers={"X-CSRFToken": csrf},
    )
    assert convert.status_code == 403


def test_manager_conversion_is_idempotent_and_preserves_identity(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    lead = next(item for item in data["leads"] if item["status"] == "ready")
    payload = {
        "customer_need": "Establish a governed AI roadmap",
        "scope_summary": "Assessment and prioritized plan",
        "primary_contact": data["contacts"][0]["id"],
        "current_value": "25000",
        "currency": "USD",
        "service_line": data["reference"]["services"][0][0],
        "expected_close_date": str(date.today() + timedelta(days=30)),
    }
    first = client.post(f'/api/v1/leads/{lead["lead_id"]}/convert/', json=payload, headers={"X-CSRFToken": csrf})
    assert first.status_code == 200, first.text
    assert first.json()["id"] == lead["id"]
    second = client.post(f'/api/v1/leads/{lead["lead_id"]}/convert/', json=payload, headers={"X-CSRFToken": csrf})
    assert second.status_code == 200
    assert second.json()["opportunity_id"] == first.json()["opportunity_id"]


def test_internal_note_does_not_change_client_interaction(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    opportunity = data["opportunities"][0]
    before = opportunity["last_client_interaction"]
    response = client.post(
        "/api/v1/activities/",
        json={
            "pursuit": opportunity["id"],
            "company": opportunity["company_id"],
            "activity_type": "Internal note",
            "direction": "Outbound",
            "subject": "Internal qualification review",
            "notes": "No customer contact occurred.",
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 201, response.text
    refreshed = client.get("/api/v1/bootstrap/").json()
    current = next(item for item in refreshed["opportunities"] if item["id"] == opportunity["id"])
    assert current["last_client_interaction"] == before
