"""Generate a deterministic disposable scale profile for ATPLCRM benchmarks."""
from __future__ import annotations

import argparse
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from .database import engine
from .models import Company, Contact, Lead, Opportunity, Pursuit, Tenant, User
from .settings import get_settings


def chunks(rows, size=1000):
    for start in range(0, len(rows), size): yield rows[start:start + size]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contacts", type=int, default=20_000)
    parser.add_argument("--leads", type=int, default=5_000)
    parser.add_argument("--opportunities", type=int, default=5_000)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    if args.confirm != "SCALE-DISPOSABLE": raise SystemExit("Use only in a disposable workspace: --confirm SCALE-DISPOSABLE")
    if max(args.contacts, args.leads, args.opportunities) > 100_000 or min(args.contacts, args.leads, args.opportunities) < 0: raise SystemExit("Counts must be between 0 and 100,000.")
    if args.opportunities and not args.contacts: raise SystemExit("At least one contact is required when generating opportunities.")
    settings = get_settings(); now = datetime.now(timezone.utc); today = date.today()
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.key == settings.tenant_key))
        if not tenant: raise SystemExit("Seed the disposable workspace before generating scale data.")
        users = db.scalars(select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True))).all()
        if not users: raise SystemExit("No active users exist in the disposable workspace.")
        if db.scalar(select(Company.id).where(Company.tenant_id == tenant.id, Company.domain == "scale-00000.benchmark.invalid")):
            raise SystemExit("Scale data already exists. Reset the disposable workspace before regenerating it.")
        actor = next((row for row in users if row.level == "Administrator"), users[0]); companies_count = max(100, (args.contacts + 19) // 20)
        company_ids = [uuid.uuid4() for _ in range(companies_count)]
        audit = {"tenant_id": tenant.id, "created_at": now, "updated_at": now, "created_by_id": actor.id, "updated_by_id": actor.id, "is_deleted": False}
        companies = [{**audit, "id": identifier, "name": f"Scale Benchmark Company {index:05d}", "domain": f"scale-{index:05d}.benchmark.invalid", "company_type": "Prospect", "industry": "Technology", "country": "United States" if index % 2 else "India", "global_account_name": "", "primary_region": "", "owner_id": users[index % len(users)].id} for index, identifier in enumerate(company_ids)]
        for batch in chunks(companies): db.execute(insert(Company), batch)
        contact_ids = [uuid.uuid4() for _ in range(args.contacts)]
        contacts = [{**audit, "id": identifier, "company_id": company_ids[index % companies_count], "first_name": f"Scale{index:05d}", "last_name": "Contact", "email": f"scale.contact.{index:05d}@benchmark.invalid", "job_title": "Director", "seniority": "Director", "phone": "", "mobile": "", "linkedin_url": "", "country": "United States", "city": "", "owner_id": users[index % len(users)].id, "sourced_by_id": actor.id, "source_channel": "Marketing campaign", "source_detail": "Scale benchmark", "first_contacted_at": None, "engagement_status": "Not contacted", "do_not_contact": False, "consent_basis": "Business card or event", "notes": ""} for index, identifier in enumerate(contact_ids)]
        for batch in chunks(contacts): db.execute(insert(Contact), batch)
        total_pursuits = args.leads + args.opportunities; pursuit_ids = [uuid.uuid4() for _ in range(total_pursuits)]; lead_ids = [uuid.uuid4() for _ in range(total_pursuits)]
        pursuits = [{**audit, "id": identifier, "name": f"Scale {'Lead' if index < args.leads else 'Opportunity'} {index:05d}", "company_id": company_ids[index % companies_count], "owner_id": users[index % len(users)].id, "sourced_by_id": actor.id, "holder_id": users[(index + 1) % len(users)].id, "ball_since": now - timedelta(days=index % 30), "next_action": "Benchmark follow-up", "action_type": "Call", "action_date": today + timedelta(days=index % 60 + 1), "priority": ("High", "Medium", "Low")[index % 3], "source_channel": "Marketing campaign", "source_detail": "Scale benchmark dataset", "blocker": "None", "blocker_owner_id": None, "blocked_since": None, "resolution_action": "", "last_client_interaction": now - timedelta(days=index % 40), "next_meeting": None, "first_contacted_at": now - timedelta(days=index % 20), "ready_at": None, "validated_at": now - timedelta(days=index % 15) if index >= args.leads else None, "presales_assigned_at": None, "proposal_sent_at": None, "closed_at": None, "version": 1} for index, identifier in enumerate(pursuit_ids)]
        for batch in chunks(pursuits): db.execute(insert(Pursuit), batch)
        leads = [{**audit, "id": lead_ids[index], "pursuit_id": pursuit_ids[index], "status": "working" if index < args.leads else "closed", "area_of_interest": "Scale benchmark", "outcome": "" if index < args.leads else "Converted", "reason": "", "revisit_date": None} for index in range(total_pursuits)]
        for batch in chunks(leads): db.execute(insert(Lead), batch)
        stages = ("discovery", "presales", "proposal", "negotiation", "contract")
        opportunities = []
        for offset in range(args.opportunities):
            index = args.leads + offset; stage = stages[offset % len(stages)]; value = Decimal(25_000 + (offset % 200) * 1_000)
            opportunities.append({**audit, "id": uuid.uuid4(), "pursuit_id": pursuit_ids[index], "origin_lead_id": lead_ids[index], "stage": stage, "opportunity_type": "New logo", "customer_need": "Scale benchmark customer need", "scope_summary": "Scale benchmark scope", "primary_contact_id": contact_ids[offset % len(contact_ids)], "service_line": "Data engineering", "engagement_type": "Fixed price", "current_value": value, "currency": "USD", "fx_rate": Decimal("1"), "value_usd": value, "expected_close_date": today + timedelta(days=offset % 365 + 1), "probability": {"discovery":20,"presales":35,"proposal":50,"negotiation":70,"contract":85}[stage], "probability_stage_default": {"discovery":20,"presales":35,"proposal":50,"negotiation":70,"contract":85}[stage], "probability_note": "", "gross_margin_pct": Decimal("35"), "restricted": False, "restriction_reason": "", "revisit_date": None, "loss_reason": "", "competitor_name": "", "competitor_status": "None known", "contract_number": "", "contract_date": None, "project_start": None, "duration_months": None, "handoff_notes": "", "approval_recorded": False, "approval_note": "", "close_notes": "", "final_evidence_artifact_id": None})
        for batch in chunks(opportunities): db.execute(insert(Opportunity), batch)
        db.commit(); print(f"Scale profile added: {companies_count} companies, {args.contacts} contacts, {args.leads} leads, {args.opportunities} opportunities.")


if __name__ == "__main__": main()
