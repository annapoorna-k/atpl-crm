from datetime import datetime, timezone

from conftest import login


def relogin(client, email):
    client.cookies.clear()
    return login(client, email)


def test_documents_email_sharing_versions_and_library(client):
    csrf = login(client, "alex@atplcrm.local")
    data = client.get("/api/v1/bootstrap/").json()
    pursuit = next(row for row in data["opportunities"] if row["can_work"])
    contact = next(row for row in data["contacts"] if row["company_id"] == pursuit["company_id"])

    linked = client.post("/api/v1/artifacts/links/", json={
        "pursuit": pursuit["id"], "title": "Client proposal", "artifact_type": "Proposal",
        "storage_link": "https://example.sharepoint.com/proposal", "is_reusable": True,
    }, headers={"X-CSRFToken": csrf})
    assert linked.status_code == 201, linked.text
    artifact_id = linked.json()["id"]

    csrf = relogin(client, "maya@atplcrm.local")
    denied = client.post(f"/api/v1/artifacts/{artifact_id}/approve/", headers={"X-CSRFToken": csrf})
    assert denied.status_code == 403
    csrf = relogin(client, "james@atplcrm.local")
    assert client.post(f"/api/v1/artifacts/{artifact_id}/approve/", headers={"X-CSRFToken": csrf}).status_code == 200
    csrf = relogin(client, "alex@atplcrm.local")
    shared = client.post(f"/api/v1/artifacts/{artifact_id}/share/", json={"contact_ids": [contact["id"]]}, headers={"X-CSRFToken": csrf})
    assert shared.status_code == 200, shared.text

    version = client.post(f"/api/v1/artifacts/{artifact_id}/versions/link/", json={
        "pursuit": pursuit["id"], "title": "Client proposal", "artifact_type": "Proposal",
        "storage_link": "https://example.sharepoint.com/proposal-v2", "is_reusable": True,
    }, headers={"X-CSRFToken": csrf})
    assert version.status_code == 201, version.text
    assert client.post(f"/api/v1/artifacts/{artifact_id}/versions/link/", json={
        "pursuit": pursuit["id"], "title": "Branch", "artifact_type": "Proposal",
        "storage_link": "https://example.sharepoint.com/branch",
    }, headers={"X-CSRFToken": csrf}).status_code == 409

    uploaded = client.post("/api/v1/artifacts/uploads/", data={
        "pursuit": pursuit["id"], "title": "Architecture", "artifact_type": "Technical architecture",
    }, files={"file": ("architecture.pdf", b"%PDF-1.4 synthetic", "application/pdf")}, headers={"X-CSRFToken": csrf})
    assert uploaded.status_code == 201, uploaded.text
    assert client.get(f"/api/v1/artifacts/{uploaded.json()['id']}/download/").content == b"%PDF-1.4 synthetic"

    email = client.post("/api/v1/artifacts/emails/", data={
        "pursuit": pursuit["id"], "subject": "Proposal sent", "message_reference": "outlook-item-123",
        "email_date": datetime.now(timezone.utc).isoformat(), "direction": "Outbound",
        "participants": '["client@example.com","alex@atplcrm.local"]', "classification": "Proposal sent",
        "recipient_contact_ids": f'["{contact["id"]}"]',
    }, files=[("attachments", ("pricing.xlsx", b"synthetic workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))], headers={"X-CSRFToken": csrf})
    assert email.status_code == 201, email.text
    assert len(email.json()["attachment_ids"]) == 1
    register = client.get(f"/api/v1/artifacts/register/?pursuit_id={pursuit['id']}").json()
    assert any(row["id"] == artifact_id and row["recipients"][0]["id"] == contact["id"] for row in register)
    assert any(row["kind"] == "Linked email" and row["email_classification"] == "Proposal sent" for row in register)
    assert any(row["parent_email_id"] == email.json()["id"] and row["artifact_type"] == "Pricing" for row in register)
    library = client.get("/api/v1/artifacts/library/?search=proposal").json()
    assert any(row["id"] == version.json()["id"] for row in library)
