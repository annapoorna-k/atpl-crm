import base64
import io
from datetime import date, timedelta
from uuid import UUID

from openpyxl import Workbook

from sqlalchemy import select
from sqlalchemy.orm import Session

from atplcrm.database import engine
from atplcrm.models import Company, Tenant, User
from atplcrm.services import stamp
from conftest import login


def test_global_search_is_tenant_scoped_and_paginated(client):
    login(client)
    response = client.get("/api/v1/data/search/?q=Northstar&page=1&page_size=2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] >= 1
    assert len(data["results"]) <= 2
    assert {item["type"] for item in data["results"]} <= {"Company", "Contact", "Lead", "Opportunity"}
    opportunities = client.get("/api/v1/data/search/?q=Predictive&entity_type=opportunities").json()
    assert opportunities["total"] == 1
    assert opportunities["results"][0]["type"] == "Opportunity"


def test_import_preview_reports_mapping_and_row_errors(client):
    csrf = login(client)
    payload = {
        "entity_type": "companies",
        "filename": "companies.csv",
        "csv_text": "Account,Country,Owner\nPreview Industries,India,missing@example.com\n",
        "mapping": {"name": "Account", "country": "Country", "owner_email": "Owner"},
    }
    response = client.post("/api/v1/data/imports/preview/", json=payload, headers={"X-CSRFToken": csrf})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_rows"] == 1 and data["valid_rows"] == 0
    assert data["errors"][0]["field"] == "owner_email"


def test_manager_imports_companies_and_history_is_recorded(client):
    csrf = login(client)
    payload = {
        "entity_type": "companies",
        "filename": "accepted-companies.csv",
        "csv_text": "name,country,owner_email,domain,industry\nImported Industries,India,alex@atplcrm.local,imported.example,Technology\n",
    }
    response = client.post("/api/v1/data/imports/", json=payload, headers={"X-CSRFToken": csrf})
    assert response.status_code == 201, response.text
    assert response.json()["imported_rows"] == 1
    history = client.get("/api/v1/data/imports/").json()
    assert history[0]["filename"] == "accepted-companies.csv"
    assert any(item["name"] == "Imported Industries" for item in client.get("/api/v1/bootstrap/").json()["companies"])


def test_standard_user_cannot_run_import(client):
    csrf = login(client, "maya@atplcrm.local")
    response = client.post("/api/v1/data/imports/", json={"entity_type": "companies", "filename": "denied.csv", "csv_text": "name,country,owner_email\nDenied,India,maya@atplcrm.local\n"}, headers={"X-CSRFToken": csrf})
    assert response.status_code == 403


def test_duplicate_review_merge_and_quality_dashboard(client):
    csrf = login(client)
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.key == "test-workspace"))
        owner = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == "alex@atplcrm.local"))
        duplicate = Company(**stamp(owner), name="Northstar Industries Holdings", country="United States", domain="northstar.example", owner_id=owner.id)
        db.add(duplicate); db.commit(); duplicate_id = str(duplicate.id)
    review = client.get("/api/v1/data/duplicates/")
    assert review.status_code == 200
    group = next(group for group in review.json()["groups"] if group["match_type"] == "Company domain" and group["match_value"] == "northstarexample")
    primary_id = next(record["id"] for record in group["records"] if record["id"] != duplicate_id)
    merged = client.post("/api/v1/data/duplicates/companies/merge/", json={"primary_id": primary_id, "duplicate_id": duplicate_id}, headers={"X-CSRFToken": csrf})
    assert merged.status_code == 200, merged.text
    quality = client.get("/api/v1/data/quality/")
    assert quality.status_code == 200
    assert 0 <= quality.json()["score"] <= 100
    assert "contacts_missing_email" in quality.json()["metrics"]


def test_lead_import_validates_future_action_date(client):
    csrf = login(client)
    payload = {
        "entity_type": "leads",
        "filename": "leads.csv",
        "csv_text": f"name,company_name,owner_email,next_action,action_type,action_date,source_channel\nImported lead,Northstar Industries,alex@atplcrm.local,Call sponsor,Call,{date.today() + timedelta(days=5)},LinkedIn\n",
    }
    response = client.post("/api/v1/data/imports/", json=payload, headers={"X-CSRFToken": csrf})
    assert response.status_code == 201, response.text
    assert response.json()["imported_rows"] == 1


def test_excel_contact_import_preserves_complete_relationship_fields(client):
    csrf = login(client)
    workbook = Workbook(); sheet = workbook.active
    headers = ["company_name", "first_name", "last_name", "country", "owner_email", "sourced_by_email", "email", "job_title", "seniority", "phone", "mobile", "linkedin_url", "city", "source_channel", "source_detail", "engagement_status", "do_not_contact", "consent_basis", "notes"]
    sheet.append(headers)
    sheet.append(["Northstar Industries", "Excel", "Contact", "United States", "alex@atplcrm.local", "maya@atplcrm.local", "excel.contact@example.com", "VP Operations", "VP or Head", "+1 555 0188", "+1 555 0189", "https://linkedin.com/in/excel-contact", "Detroit", "Exhibition or event", "Manufacturing Summit", "Engaged", "No", "Business card or event", "Prefers email"])
    stream = io.BytesIO(); workbook.save(stream)
    payload = {"entity_type": "contacts", "filename": "contacts.xlsx", "file_type": "xlsx", "file_content": base64.b64encode(stream.getvalue()).decode(), "mapping": {}}
    preview = client.post("/api/v1/data/imports/preview/", json=payload, headers={"X-CSRFToken": csrf})
    assert preview.status_code == 200, preview.text
    assert preview.json()["valid_rows"] == 1
    response = client.post("/api/v1/data/imports/", json=payload, headers={"X-CSRFToken": csrf})
    assert response.status_code == 201, response.text
    contact = next(item for item in client.get("/api/v1/bootstrap/").json()["contacts"] if item["email"] == "excel.contact@example.com")
    assert contact["sourced_by"] == "Maya Patel"
    assert contact["seniority"] == "VP or Head"
    assert contact["source_detail"] == "Manufacturing Summit"
    assert contact["consent_basis"] == "Business card or event"


def test_fuzzy_duplicate_can_be_field_merged_or_dismissed_and_quality_filters(client):
    csrf = login(client)
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.key == "test-workspace")); owner = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == "alex@atplcrm.local"))
        first = Company(**stamp(owner), name="Meridian Analytics Group", country="United Kingdom", domain="meridian-one.example", industry="Technology", owner_id=owner.id)
        second = Company(**stamp(owner), name="Meridian Analytic Group", country="United Kingdom", domain="meridian-two.example", industry="Consulting", owner_id=owner.id)
        distinct_a = Company(**stamp(owner), name="Summit Advisory Partners", country="India", domain="summit-a.example", owner_id=owner.id)
        distinct_b = Company(**stamp(owner), name="Summit Advisery Partners", country="India", domain="summit-b.example", owner_id=owner.id)
        db.add_all([first, second, distinct_a, distinct_b]); db.commit()
        ids = [str(item.id) for item in (first, second, distinct_a, distinct_b)]
    review = client.get("/api/v1/data/duplicates/").json()
    merge_group = next(group for group in review["groups"] if {record["id"] for record in group["records"]} == set(ids[:2]))
    assert merge_group["confidence"] >= 88 and "Similar company name" in merge_group["match_reasons"]
    merged = client.post("/api/v1/data/duplicates/companies/merge/", json={"primary_id": ids[0], "duplicate_id": ids[1], "field_sources": {"domain": ids[1], "industry": ids[0]}}, headers={"X-CSRFToken": csrf})
    assert merged.status_code == 200, merged.text
    with Session(engine) as db:
        surviving = db.get(Company, UUID(ids[0])); assert surviving.domain == "meridian-two.example" and surviving.industry == "Technology"
    dismissed = client.post("/api/v1/data/duplicates/companies/dismiss/", json={"first_id": ids[2], "second_id": ids[3], "reason": "Separate legal entities with different registrations."}, headers={"X-CSRFToken": csrf})
    assert dismissed.status_code == 200, dismissed.text
    refreshed = client.get("/api/v1/data/duplicates/").json()
    assert not any({record["id"] for record in group["records"]} == set(ids[2:]) for group in refreshed["groups"])
    quality = client.get("/api/v1/data/quality/?severity=low&entity_type=company&page_size=2").json()
    assert quality["filtered_issue_count"] >= len(quality["issues"])
    assert all(item["severity"] == "Low" and item["type"] == "Company" for item in quality["issues"])
