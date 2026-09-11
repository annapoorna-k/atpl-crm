from conftest import login

def test_administration_requires_workspace_administrator(client):
    csrf = login(client, "alex@atplcrm.local")
    response = client.post("/api/v1/admin/users/", json={"first_name": "Denied", "last_name": "User", "email": "denied@example.com", "job_title": "Tester", "level": "Standard", "password": "Temporary1234"}, headers={"X-CSRFToken": csrf})
    assert response.status_code == 403

def test_administrator_can_create_edit_and_deactivate_user(client):
    csrf = login(client, "admin@atplcrm.local")
    created = client.post("/api/v1/admin/users/", json={"first_name": "Priya", "last_name": "Nair", "email": "priya@example.com", "job_title": "Sales Operations", "level": "Manager", "password": "Temporary1234"}, headers={"X-CSRFToken": csrf})
    assert created.status_code == 201, created.text
    user = created.json(); assert user["active"] is True and user["level"] == "Manager"
    changed = client.patch(f'/api/v1/admin/users/{user["id"]}/', json={"job_title": "Revenue Operations", "level": "Standard", "is_active": False}, headers={"X-CSRFToken": csrf})
    assert changed.status_code == 200 and changed.json()["active"] is False
    data = client.get("/api/v1/bootstrap/").json()
    assert any(item["email"] == "priya@example.com" and not item["active"] for item in data["admin_users"])
    assert all(item["email"] != "priya@example.com" for item in data["users"])

def test_administrator_cannot_remove_own_access(client):
    csrf = login(client, "admin@atplcrm.local"); current = client.get("/api/v1/bootstrap/").json()["user"]
    response = client.patch(f'/api/v1/admin/users/{current["id"]}/', json={"level": "Standard"}, headers={"X-CSRFToken": csrf})
    assert response.status_code == 422

def test_reference_configuration_changes_bootstrap_contract(client):
    csrf = login(client, "admin@atplcrm.local"); data = client.get("/api/v1/bootstrap/").json()
    stage = next(item for item in data["admin_references"] if item["category"] == "stages" and item["code"] == "discovery")
    updated = client.patch(f'/api/v1/admin/references/{stage["id"]}/', json={"label": "Discovery review", "numeric_value": 25}, headers={"X-CSRFToken": csrf})
    assert updated.status_code == 200
    created = client.post("/api/v1/admin/references/", json={"category": "sources", "code": "Industry roundtable", "label": "Industry roundtable", "sort_order": 15, "active": True}, headers={"X-CSRFToken": csrf})
    assert created.status_code == 201
    reference = client.get("/api/v1/bootstrap/").json()["reference"]
    assert ["discovery", "Discovery review"] in reference["stages"] and reference["probabilities"]["discovery"] == 25
    assert ["Industry roundtable", "Industry roundtable"] in reference["sources"]

def test_usd_reporting_rate_cannot_change(client):
    csrf = login(client, "admin@atplcrm.local"); usd = next(item for item in client.get("/api/v1/bootstrap/").json()["reference"]["currencies"] if item["currency"] == "USD")
    response = client.patch(f'/api/v1/admin/rates/{usd["id"]}/', json={"rate": "1.1", "source": "Invalid base-rate change"}, headers={"X-CSRFToken": csrf})
    assert response.status_code == 422
