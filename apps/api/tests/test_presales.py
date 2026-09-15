from datetime import date, timedelta

from conftest import login


def relogin(client, email):
    client.cookies.clear()
    return login(client, email)


def test_complete_presales_assignment_review_delivery_capacity_and_cost(client):
    csrf = login(client, "james@atplcrm.local")
    data = client.get("/api/v1/bootstrap/").json()
    opportunity = data["opportunities"][0]
    omar = next(user for user in data["users"] if user["email"] == "omar@atplcrm.local")
    maya = next(user for user in data["users"] if user["email"] == "maya@atplcrm.local")
    needed_by = date.today() + timedelta(days=3)
    created = client.post(
        "/api/v1/requests/",
        json={
            "opportunity": opportunity["opportunity_id"],
            "title": "Architecture review pack",
            "request_type": "Technical solution design",
            "assigned_to": omar["id"],
            "needed_by": str(needed_by),
            "customer_meeting_date": str(needed_by + timedelta(days=1)),
            "estimated_days": "2.5",
            "notes": "Prepare the client-ready architecture.",
        },
        headers={"X-CSRFToken": csrf},
    )
    assert created.status_code == 201, created.text
    request = created.json()
    assert request["assigned_to_id"] == omar["id"] and request["status"] == "Requested"

    csrf = relogin(client, "omar@atplcrm.local")
    invalid = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "Delivered", "actual_days": "2"},
        headers={"X-CSRFToken": csrf},
    )
    assert invalid.status_code == 422
    accepted = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "Accepted", "supporting_contributor_ids": [maya["id"]]},
        headers={"X-CSRFToken": csrf},
    )
    assert accepted.status_code == 200, accepted.text
    request = accepted.json()
    assert request["contributors"] == [{"id": maya["id"], "name": maya["name"]}]
    progressed = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "In progress"},
        headers={"X-CSRFToken": csrf},
    )
    assert progressed.status_code == 200, progressed.text
    request = progressed.json()
    artifact = client.post(
        "/api/v1/artifacts/",
        json={"pursuit": request["pursuit_id"], "title": "Architecture review v1", "artifact_type": "Technical architecture", "storage_link": "https://example.com/architecture", "internal_only": False},
        headers={"X-CSRFToken": csrf},
    )
    assert artifact.status_code == 201, artifact.text
    ready = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "Ready for review", "deliverable_artifact_id": artifact.json()["id"]},
        headers={"X-CSRFToken": csrf},
    )
    assert ready.status_code == 200, ready.text
    request = ready.json()

    csrf = relogin(client, "james@atplcrm.local")
    approved = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "Approved to share", "review_note": "Reviewed for technical accuracy and client confidentiality."},
        headers={"X-CSRFToken": csrf},
    )
    assert approved.status_code == 200, approved.text
    request = approved.json()
    assert request["approved_by"] == "James Chen"

    csrf = relogin(client, "omar@atplcrm.local")
    delivered = client.patch(
        f'/api/v1/requests/{request["id"]}/',
        json={"version": request["version"], "status": "Delivered", "actual_days": "2.0", "shared_with_contact_ids": [opportunity["primary_contact_id"]]},
        headers={"X-CSRFToken": csrf},
    )
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["actual_days"] == "2.0"
    timeline = client.get(f'/api/v1/pursuits/{request["pursuit_id"]}/timeline/').json()
    assert next(item for item in timeline["artifacts"] if item["id"] == artifact.json()["id"])["shared_at"] is not None

    queue = client.get(f"/api/v1/presales/queue/?week={needed_by}&status_filter=all")
    assert queue.status_code == 200, queue.text
    assert any(item["id"] == request["id"] for item in queue.json()["requests"])
    csrf = relogin(client, "james@atplcrm.local")
    cost = client.get("/api/v1/presales/cost-report/")
    assert cost.status_code == 200, cost.text
    assert any(row["key"] == "Technical solution design" and row["actual_days"] == "2.0" for row in cost.json()["by_request_type"])
