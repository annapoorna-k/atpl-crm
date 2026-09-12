from conftest import login


def test_paginated_lists_support_filters_and_sorting(client):
    login(client)
    companies = client.get("/api/v1/productivity/lists/companies/?q=Northstar&page=1&page_size=10&sort=name&direction=asc")
    assert companies.status_code == 200, companies.text
    assert companies.json()["total"] == 1
    assert companies.json()["items"][0]["name"] == "Northstar Industries"
    opportunities = client.get("/api/v1/productivity/lists/opportunities/?status=proposal&page_size=10")
    assert opportunities.status_code == 200, opportunities.text
    assert opportunities.json()["total"] >= 1
    assert all(item["stage"] == "proposal" for item in opportunities.json()["items"])


def test_personal_saved_views_are_private_and_editable(client):
    csrf = login(client)
    created = client.post("/api/v1/productivity/views/", json={"entity_type": "opportunities", "name": "My proposals", "filters": {"status": "proposal", "owner_id": 1}}, headers={"X-CSRFToken": csrf})
    assert created.status_code == 201, created.text
    view = created.json()
    changed = client.patch(f'/api/v1/productivity/views/{view["id"]}/', json={"name": "Priority proposals", "filters": {"status": "proposal", "priority": "High"}}, headers={"X-CSRFToken": csrf})
    assert changed.status_code == 200 and changed.json()["filters"]["priority"] == "High"
    assert any(item["id"] == view["id"] for item in client.get("/api/v1/productivity/views/?entity_type=opportunities").json())
    client.delete("/api/v1/session/", headers={"X-CSRFToken": csrf})
    login(client, "maya@atplcrm.local")
    assert all(item["id"] != view["id"] for item in client.get("/api/v1/productivity/views/?entity_type=opportunities").json())


def test_manager_bulk_assignment_uses_optimistic_versions(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    lead = next(item for item in data["leads"] if item["status"] != "closed")
    omar = next(item for item in data["users"] if item["email"] == "omar@atplcrm.local")
    payload = {"pursuit_ids": [lead["id"]], "versions": {lead["id"]: lead["version"]}, "holder_id": omar["id"], "reason": "Route technical follow-up"}
    changed = client.post("/api/v1/productivity/pursuits/bulk-assignment/", json=payload, headers={"X-CSRFToken": csrf})
    assert changed.status_code == 200 and changed.json()["updated"] == 1
    conflict = client.post("/api/v1/productivity/pursuits/bulk-assignment/", json=payload, headers={"X-CSRFToken": csrf})
    assert conflict.status_code == 409


def test_standard_user_cannot_bulk_assign(client):
    csrf = login(client, "maya@atplcrm.local")
    lead = next(item for item in client.get("/api/v1/bootstrap/").json()["leads"] if item["status"] != "closed")
    response = client.post("/api/v1/productivity/pursuits/bulk-assignment/", json={"pursuit_ids": [lead["id"]], "versions": {lead["id"]: lead["version"]}, "holder_id": lead["holder_id"], "reason": "Not permitted"}, headers={"X-CSRFToken": csrf})
    assert response.status_code == 403


def test_stakeholder_roles_can_be_added_changed_and_removed(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    opportunity = data["opportunities"][0]
    contact = client.post("/api/v1/contacts/", json={"company": opportunity["company_id"], "first_name": "Jordan", "last_name": "Lee", "email": "jordan.stakeholder@example.com", "country": "United States", "owner": data["user"]["id"]}, headers={"X-CSRFToken": csrf})
    assert contact.status_code == 201, contact.text
    added = client.post(f'/api/v1/productivity/pursuits/{opportunity["id"]}/stakeholders/', json={"contact_id": contact.json()["id"], "role": "Influencer"}, headers={"X-CSRFToken": csrf})
    assert added.status_code == 201, added.text
    link = next(item for item in added.json() if item["id"] == contact.json()["id"])
    changed = client.patch(f'/api/v1/productivity/stakeholders/{link["link_id"]}/', json={"role": "Decision maker"}, headers={"X-CSRFToken": csrf})
    assert changed.status_code == 200
    assert next(item for item in changed.json() if item["id"] == contact.json()["id"])["role"] == "Decision maker"
    removed = client.delete(f'/api/v1/productivity/stakeholders/{link["link_id"]}/', headers={"X-CSRFToken": csrf})
    assert removed.status_code == 200
    assert all(item["id"] != contact.json()["id"] for item in removed.json())
    primary = opportunity["contacts"][0]
    protected = client.delete(f'/api/v1/productivity/stakeholders/{primary["link_id"]}/', headers={"X-CSRFToken": csrf})
    assert protected.status_code == 422
