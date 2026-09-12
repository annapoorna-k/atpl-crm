from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from atplcrm.database import engine
from atplcrm.models import Pursuit, Tenant
from atplcrm.notifications import weekly_summary_for_tenant
from conftest import login


def test_work_endpoint_has_complete_personal_and_exception_queues(client):
    login(client)
    response = client.get("/api/v1/work/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert set(data["my_work"]) == {
        "overdue_actions", "today_actions", "upcoming_actions", "blockers", "deliverables",
    }
    assert isinstance(data["needs_attention"], list)
    assert all({"kind", "label", "severity"} <= set(issue) for issue in data["needs_attention"])


def test_notification_preferences_are_user_configurable(client):
    csrf = login(client, "maya@atplcrm.local")
    current = client.get("/api/v1/notifications/preferences/")
    assert current.status_code == 200
    payload = current.json() | {"due_actions": False, "inactivity_days": 30, "proposal_followup_days": 10, "close_notice_days": 14}
    changed = client.patch("/api/v1/notifications/preferences/", json=payload, headers={"X-CSRFToken": csrf})
    assert changed.status_code == 200, changed.text
    assert changed.json()["due_actions"] is False
    assert changed.json()["inactivity_days"] == 30


def test_exception_scan_routes_alerts_and_records_delivery_history(client):
    login(client)
    data = client.get("/api/v1/bootstrap/").json()
    pursuit = data["opportunities"][0]
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        record = db.get(Pursuit, UUID(pursuit["id"]))
        record.owner_id = data["user"]["id"]
        record.holder_id = data["user"]["id"]
        record.action_date = date.today() - timedelta(days=1)
        record.ball_since = now - timedelta(days=16)
        record.blocker = "Customer dependency"
        record.blocker_owner_id = data["user"]["id"]
        record.blocked_since = now - timedelta(days=12)
        record.resolution_action = "Confirm dependency owner"
        record.last_client_interaction = now - timedelta(days=30)
        record.proposal_sent_at = now - timedelta(days=8)
        record.opportunity.stage = "proposal"
        record.opportunity.expected_close_date = date.today() - timedelta(days=1)
        db.commit()
    csrf = login(client, "admin@atplcrm.local")
    scanned = client.post("/api/v1/notifications/refresh/", json={}, headers={"X-CSRFToken": csrf})
    assert scanned.status_code == 200, scanned.text
    assert scanned.json()["created"] > 0
    status = client.get("/api/v1/notifications/status/").json()["latest"]
    assert status["status"] == "Succeeded"
    assert status["created_count"] == scanned.json()["created"]
    csrf = login(client)
    history = client.get("/api/v1/notifications/history/").json()
    categories = {item["category"] for item in history["items"]}
    assert {"due_actions", "stalled_pursuits", "blockers", "inactivity", "close_dates"} <= categories
    unread = next(item for item in history["items"] if not item["read"])
    read = client.post(f'/api/v1/notifications/{unread["id"]}/read/', json={}, headers={"X-CSRFToken": csrf})
    assert read.status_code == 200 and read.json()["read_at"]


def test_weekly_summary_is_deduplicated_for_leadership(client):
    with Session(engine) as db:
        tenant = db.query(Tenant).filter(Tenant.key == "test-workspace").one()
        first = weekly_summary_for_tenant(db, tenant.id)
        second = weekly_summary_for_tenant(db, tenant.id)
        db.commit()
    assert first > 0
    assert second == 0
    login(client, "sarah@atplcrm.local")
    history = client.get("/api/v1/notifications/history/").json()
    assert any(item["category"] == "weekly_summary" for item in history["items"])
