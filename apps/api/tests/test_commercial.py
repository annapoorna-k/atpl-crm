from conftest import login


def test_partner_terms_drive_net_value_and_management_reports(client):
    csrf = login(client, "alex@atplcrm.local")
    data = client.get("/api/v1/bootstrap/").json()
    opportunity = next(row for row in data["opportunities"] if row["name"] == "Predictive maintenance platform")
    owner = data["user"]["id"]

    company_response = client.post(
        "/api/v1/companies/",
        json={"name": "Commercial Test Partner", "company_type": "Referral partner", "country": "United Kingdom", "owner": owner},
        headers={"X-CSRFToken": csrf},
    )
    assert company_response.status_code == 201, company_response.text
    company = company_response.json()
    contact_response = client.post(
        "/api/v1/contacts/",
        json={"company": company["id"], "first_name": "Taylor", "last_name": "Partner", "email": "commercial.partner@example.com", "country": "United Kingdom", "owner": owner},
        headers={"X-CSRFToken": csrf},
    )
    assert contact_response.status_code == 201, contact_response.text
    contact = contact_response.json()

    partner_response = client.post(
        f'/api/v1/opportunities/{opportunity["opportunity_id"]}/partners/',
        json={"company_id": company["id"], "contact_id": contact["id"], "role": "Referral source", "introduced": True, "fee_basis": "Percentage of contract value", "share_pct": "10", "fixed_fee": "0", "applies_to": "This contract only", "status": "Verbally agreed", "terms_notes": "Commercial test terms"},
        headers={"X-CSRFToken": csrf},
    )
    assert partner_response.status_code == 201, partner_response.text
    commercial = partner_response.json()
    assert commercial["total_partner_share_pct"] == "10.00"
    assert commercial["partner_deduction_local"] == "18500.00"
    assert commercial["net_value_usd"] == "166500.00"
    assert commercial["partners"][0]["introduced"] is True

    report = client.get("/api/v1/commercial/reports/undocumented-partners/")
    assert report.status_code == 200
    assert any(row["partner"] == "Commercial Test Partner" for row in report.json())


def test_opportunity_rate_change_is_guarded_and_probability_keeps_stage_default(client):
    csrf = login(client, "alex@atplcrm.local")
    opportunities = client.get("/api/v1/bootstrap/").json()["opportunities"]
    opportunity = next(row for row in opportunities if row["name"] == "Predictive maintenance platform")
    invalid_rate = client.post(
        f'/api/v1/opportunities/{opportunity["opportunity_id"]}/rate/',
        json={"rate": "1.1", "reason": "USD must stay fixed"},
        headers={"X-CSRFToken": csrf},
    )
    assert invalid_rate.status_code == 422

    overridden = client.post(
        f'/api/v1/opportunities/{opportunity["opportunity_id"]}/probability/',
        json={"probability": 63, "reason": "Client confirmed budget"},
        headers={"X-CSRFToken": csrf},
    )
    assert overridden.status_code == 200, overridden.text
    body = overridden.json()
    assert body["probability"] == 63
    assert body["stage_probability"] == 50
    assert body["probability_note"] == "Client confirmed budget"
