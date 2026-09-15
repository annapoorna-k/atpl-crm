from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from atplcrm.database import engine
from atplcrm.models import Pursuit
from conftest import login


def test_action_completion_preserves_history_and_replaces_the_plan(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    pursuit = data["opportunities"][0]
    next_holder = data["users"][1]
    response = client.post(
        f'/api/v1/pipeline/pursuits/{pursuit["id"]}/actions/complete/',
        json={
            "version": pursuit["version"],
            "outcome": "Completed",
            "note": "Client confirmed the next step.",
            "next_holder": next_holder["id"],
            "next_action": "Prepare the solution workshop",
            "next_action_type": data["reference"]["actions"][0][0],
            "next_action_date": str(date.today() + timedelta(days=3)),
        },
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200, response.text
    assert response.json()["summary"] == pursuit["next_action"]
    refreshed = client.get("/api/v1/bootstrap/").json()
    current = next(row for row in refreshed["opportunities"] if row["id"] == pursuit["id"])
    assert current["next_action"] == "Prepare the solution workshop"
    assert current["holder_id"] == next_holder["id"]
    assert current["version"] == pursuit["version"] + 1
    timeline = client.get(f'/api/v1/pursuits/{pursuit["id"]}/timeline/').json()
    assert any(row["outcome"] == "Completed" for row in timeline["completed_actions"])


def test_action_completion_rejects_stale_versions_and_non_future_dates(client):
    csrf = login(client)
    data = client.get("/api/v1/bootstrap/").json()
    pursuit = data["opportunities"][0]
    payload = {
        "version": pursuit["version"] - 1,
        "outcome": "Completed",
        "next_holder": data["user"]["id"],
        "next_action": "Follow up",
        "next_action_type": data["reference"]["actions"][0][0],
        "next_action_date": str(date.today() + timedelta(days=2)),
    }
    assert client.post(f'/api/v1/pipeline/pursuits/{pursuit["id"]}/actions/complete/', json=payload, headers={"X-CSRFToken": csrf}).status_code == 409
    payload["version"] = pursuit["version"]
    payload["next_action_date"] = str(date.today())
    assert client.post(f'/api/v1/pipeline/pursuits/{pursuit["id"]}/actions/complete/', json=payload, headers={"X-CSRFToken": csrf}).status_code == 422


def test_stage_changes_use_optimistic_concurrency_and_capture_reason(client):
    csrf = login(client)
    pursuit = client.get("/api/v1/bootstrap/").json()["opportunities"][0]
    old_stage, old_version = pursuit["stage"], pursuit["version"]
    response = client.post(
        f'/api/v1/opportunities/{pursuit["opportunity_id"]}/stage/',
        json={"stage": "hold", "version": old_version, "reason": "Awaiting customer budget", "revisit_date": str(date.today() + timedelta(days=7))},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200, response.text
    assert response.json()["version"] == old_version + 1
    stale = client.post(
        f'/api/v1/opportunities/{pursuit["opportunity_id"]}/stage/',
        json={"stage": old_stage, "version": old_version, "reason": "Stale browser"},
        headers={"X-CSRFToken": csrf},
    )
    assert stale.status_code == 409
    timeline = client.get(f'/api/v1/pursuits/{pursuit["id"]}/timeline/').json()
    assert any(row["action"] == "Stage changed" and row["detail"] == "Awaiting customer budget" for row in timeline["events"])
    with Session(engine) as db:
        record = db.scalar(select(Pursuit).where(Pursuit.id == UUID(pursuit["id"])))
        record.opportunity.stage = old_stage
        record.version = old_version
        db.commit()


def test_report_tracks_exactly_seven_lifecycle_milestones(client):
    login(client)
    report = client.get("/api/v1/pipeline/milestones/")
    assert report.status_code == 200, report.text
    rows = report.json()
    assert [row["key"] for row in rows] == [
        "lead_created", "first_contacted", "ready_for_validation", "validated",
        "presales_assigned", "proposal_sent", "closed",
    ]
    assert [row["target_working_days"] for row in rows] == [0, 3, 15, 5, 3, 20, 45]
    assert all("count" in row and "median_working_days" in row and "healthy" in row for row in rows)


def test_admin_calendar_and_management_movement_report(client):
    csrf = login(client, "admin@atplcrm.local")
    holiday = str(date.today() + timedelta(days=10))
    changed = client.patch(
        "/api/v1/admin/working-calendar/",
        json={"working_weekdays": [6, 0, 1, 2, 3], "holidays": [holiday]},
        headers={"X-CSRFToken": csrf},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json() == {"working_weekdays": [0, 1, 2, 3, 6], "holidays": [holiday]}
    assert client.get("/api/v1/bootstrap/").json()["working_calendar"]["holidays"] == [holiday]
    report = client.get("/api/v1/pipeline/movement/?period=90d")
    assert report.status_code == 200, report.text
    assert {"move_count", "regression_count", "transitions", "current_stage_age", "moves", "calendar"} <= report.json().keys()
    restored = client.patch(
        "/api/v1/admin/working-calendar/",
        json={"working_weekdays": [0, 1, 2, 3, 4], "holidays": []},
        headers={"X-CSRFToken": csrf},
    )
    assert restored.status_code == 200
