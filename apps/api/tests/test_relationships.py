from datetime import date, datetime, timedelta, timezone

from conftest import login


def create_owned_contact(client, csrf, suffix):
    data = client.get("/api/v1/bootstrap/").json()
    owner = next(user for user in data["users"] if user["email"] == "maya@atplcrm.local")
    company = client.post(
        "/api/v1/companies/",
        json={"name": f"Relationship Completion {suffix}", "company_type": "Prospect", "industry": "Manufacturing", "country": "United States", "global_account_name": "RCT Global", "primary_region": "United States", "owner": owner["id"]},
        headers={"X-CSRFToken": csrf},
    ).json()
    response = client.post(
        "/api/v1/contacts/",
        json={"company": company["id"], "first_name": "Casey", "last_name": suffix, "email": f"casey.{suffix.lower()}@example.com", "job_title": "VP Operations", "seniority": "VP or Head", "phone": "+1 555 0100", "mobile": "+1 555 0101", "linkedin_url": "https://linkedin.com/in/casey-buyer", "country": "United States", "city": "Detroit", "owner": owner["id"], "sourced_by": data["user"]["id"], "source_channel": "Exhibition or event", "source_detail": "Industry summit 2026", "engagement_status": "Not contacted", "consent_basis": "Business card or event", "notes": "Prefers concise technical summaries."},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 201, response.text
    return company, response.json(), owner


def test_contact_completion_collision_context_and_do_not_contact_override(client):
    csrf = login(client, "admin@atplcrm.local")
    company, contact, owner = create_owned_contact(client, csrf, "Collision")
    assert contact["sourced_by"] == "System Administrator"
    assert contact["seniority"] == "VP or Head"

    lead_response = client.post(
        "/api/v1/leads/",
        json={"name": "Collision context pursuit", "company": company["id"], "owner": owner["id"], "holder": contact["sourced_by_id"], "next_action": "Follow up with buyer", "action_type": "Call", "action_date": (date.today() + timedelta(days=2)).isoformat(), "source_channel": "Exhibition or event", "source_detail": "Industry summit 2026", "priority": "Medium", "area_of_interest": "Operations transformation"},
        headers={"X-CSRFToken": csrf},
    )
    assert lead_response.status_code == 201, lead_response.text
    pursuit = lead_response.json()
    first = client.post(
        "/api/v1/activities/",
        json={"company": company["id"], "contact": contact["id"], "pursuit": pursuit["id"], "activity_type": "Email", "direction": "Outbound", "outcome": "No response", "subject": "Initial introduction", "notes": "Sent overview."},
        headers={"X-CSRFToken": csrf},
    )
    assert first.status_code == 201, first.text
    assert owner["name"] in first.json()["warning"]

    contact = next(item for item in client.get("/api/v1/bootstrap/").json()["contacts"] if item["id"] == contact["id"])
    assert contact["first_contacted_at"]
    assert contact["engagement_status"] == "Contacted no response"
    assert contact["last_outbound_at"]

    blocked = client.patch(f'/api/v1/contacts/{contact["id"]}/', json={"do_not_contact": True}, headers={"X-CSRFToken": csrf})
    assert blocked.status_code == 200, blocked.text
    denied = client.post("/api/v1/activities/", json={"company": company["id"], "contact": contact["id"], "activity_type": "Call", "direction": "Outbound", "outcome": "Responded", "subject": "Follow-up"}, headers={"X-CSRFToken": csrf})
    assert denied.status_code == 422
    allowed = client.post("/api/v1/activities/", json={"company": company["id"], "contact": contact["id"], "activity_type": "Call", "direction": "Outbound", "outcome": "Responded", "subject": "Approved follow-up", "override_reason": "Contact explicitly requested this callback."}, headers={"X-CSRFToken": csrf})
    assert allowed.status_code == 201, allowed.text
    assert "Last outbound touch" in allowed.json()["warning"]
    assert pursuit["name"] in allowed.json()["warning"]


def test_relationship_histories_are_scoped_paginated_and_keep_backdated_order(client):
    csrf = login(client, "admin@atplcrm.local")
    company, contact, _owner = create_owned_contact(client, csrf, "History")
    now = datetime.now(timezone.utc)
    for hours, subject, activity_type in [(3, "Older note", "Internal note"), (2, "First client touch", "Email"), (1, "Latest meeting", "Meeting")]:
        response = client.post("/api/v1/activities/", json={"company": company["id"], "contact": contact["id"], "activity_type": activity_type, "direction": "Outbound", "activity_date": (now - timedelta(hours=hours)).isoformat(), "outcome": "Responded", "subject": subject}, headers={"X-CSRFToken": csrf})
        assert response.status_code == 201, response.text

    page_one = client.get(f'/api/v1/activities/?contact={contact["id"]}&page=1&page_size=2').json()
    page_two = client.get(f'/api/v1/activities/?contact={contact["id"]}&page=2&page_size=2').json()
    company_history = client.get(f'/api/v1/activities/?company={company["id"]}&page=1&page_size=20').json()
    assert page_one["total"] == 3 and page_one["pages"] == 2
    assert [item["subject"] for item in page_one["items"]] == ["Latest meeting", "First client touch"]
    assert [item["subject"] for item in page_two["items"]] == ["Older note"]
    assert company_history["total"] == 3
    refreshed = next(item for item in client.get("/api/v1/bootstrap/").json()["contacts"] if item["id"] == contact["id"])
    assert refreshed["touch_count"] == 2
    assert refreshed["engagement_status"] == "Meeting held"
