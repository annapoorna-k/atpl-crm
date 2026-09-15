import os
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from .constants import PROBABILITIES, REFERENCE_DEFAULTS, SERVICES, SOURCES
from .database import engine
from .models import Activity, CommercialSetting, Company, Contact, ExchangeRate, Lead, Opportunity, Pursuit, PursuitContact, TeamRole, Tenant, User, ValueHistory, WorkingCalendar, WorkspaceReference
from .services import stamp
from .settings import get_settings

def ensure_references(db: Session, tenant: Tenant, actor: User) -> None:
    existing = set(db.execute(select(WorkspaceReference.category, WorkspaceReference.code).where(WorkspaceReference.tenant_id == tenant.id)).all())
    for category, options in REFERENCE_DEFAULTS.items():
        for order, (code, label, numeric_value) in enumerate(options):
            if (category, code) not in existing: db.add(WorkspaceReference(**stamp(actor), category=category, code=code, label=label, numeric_value=numeric_value, sort_order=order * 10))
    if not db.scalar(select(CommercialSetting.id).where(CommercialSetting.tenant_id == tenant.id)):
        db.add(CommercialSetting(**stamp(actor), partner_share_warning_pct=Decimal("40"), fx_movement_notice_pct=Decimal("5")))
    if not db.scalar(select(WorkingCalendar.id).where(WorkingCalendar.tenant_id == tenant.id)):
        db.add(WorkingCalendar(**stamp(actor), working_weekdays=[0,1,2,3,4], holidays=[]))


def seed() -> None:
    settings = get_settings()
    if settings.app_mode != "local-demo":
        raise SystemExit("Demo seeding requires APP_MODE=local-demo.")
    if not settings.demo_password or len(settings.demo_password) < 12:
        raise SystemExit("Set DEMO_PASSWORD to at least 12 characters.")
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.key == settings.tenant_key))
        if tenant:
            if tenant.instance_type != settings.instance_type: raise SystemExit("Existing deployment type cannot be changed without migration.")
            if db.scalar(select(User.id).where(User.tenant_id == tenant.id).limit(1)):
                admin = db.scalar(select(User).where(User.tenant_id == tenant.id, User.level == "Administrator", User.is_active.is_(True)))
                if admin: ensure_references(db, tenant, admin); db.commit()
                print("Demo data already present; reference defaults checked without changing user data.")
                return
        else:
            tenant = Tenant(key=settings.tenant_key, instance_type=settings.instance_type); db.add(tenant); db.flush()
        password = PasswordHash.recommended().hash(settings.demo_password)
        people = [("alex", "Alex", "Morgan", "Manager", "Head of Sales"), ("maya", "Maya", "Patel", "Standard", "Account Executive"), ("james", "James", "Chen", "Manager", "Head of Pre-Sales"), ("sarah", "Sarah", "Williams", "Executive", "Chief Executive"), ("omar", "Omar", "Hassan", "Standard", "Technical Lead"), ("admin", "System", "Administrator", "Administrator", "Workspace Administration")]
        users = []
        for handle, first, last, level, title in people:
            item = User(username=f"{handle}@atplcrm.local", email=f"{handle}@atplcrm.local", password=password, first_name=first, last_name=last, tenant_id=tenant.id, level=level, job_title=title)
            db.add(item); users.append(item)
        db.flush(); alex, maya, james, sarah, omar, admin = users
        ensure_references(db, tenant, admin)
        rates = {"USD": "1", "AED": "0.272294", "SAR": "0.266667", "INR": "0.0119", "BHD": "2.65957", "EUR": "1.09", "GBP": "1.28"}
        for currency, rate in rates.items():
            if settings.instance_type == "US" and currency != "USD": continue
            db.add(ExchangeRate(**stamp(admin), currency=currency, rate=Decimal(rate)))
        company = Company(**stamp(maya), name="Northstar Industries", industry="Manufacturing", country="United States", domain="northstar.example", company_type="Prospect", owner_id=maya.id)
        db.add(company); db.flush()
        contact = Contact(**stamp(maya), company_id=company.id, first_name="Elena", last_name="Rodriguez", email="elena@northstar.example", country="United States", job_title="Chief Digital Officer", owner_id=maya.id, sourced_by_id=maya.id, source_channel="LinkedIn", engagement_status="Engaged")
        db.add(contact); db.flush()
        pursuit = Pursuit(**stamp(maya), name="Predictive maintenance platform", company_id=company.id, owner_id=maya.id, sourced_by_id=maya.id, holder_id=alex.id, source_channel="LinkedIn", next_action="Follow up on proposal feedback", action_type="Call", action_date=date.today() + timedelta(days=2))
        db.add(pursuit); db.flush()
        lead = Lead(**stamp(maya), pursuit_id=pursuit.id, status="closed", outcome="Converted", area_of_interest="Predictive maintenance")
        db.add(lead); db.flush()
        opportunity = Opportunity(**stamp(alex), pursuit_id=pursuit.id, origin_lead_id=lead.id, stage="proposal", customer_need="Reduce unplanned downtime", scope_summary="Focused pilot and phased rollout", primary_contact_id=contact.id, service_line=SERVICES[1], current_value=Decimal("185000"), currency="USD", fx_rate=Decimal("1"), value_usd=Decimal("185000"), expected_close_date=date.today() + timedelta(days=30), probability=PROBABILITIES["proposal"], probability_stage_default=PROBABILITIES["proposal"])
        db.add(opportunity); db.flush()
        db.add_all([ValueHistory(**stamp(alex), opportunity_id=opportunity.id, value_type="Initial estimate", amount=Decimal("185000"), currency="USD", fx_rate=Decimal("1")), PursuitContact(**stamp(maya), pursuit_id=pursuit.id, contact_id=contact.id, role="Champion"), TeamRole(**stamp(alex), pursuit_id=pursuit.id, user_id=james.id, role="Pre-sales owner"), TeamRole(**stamp(alex), pursuit_id=pursuit.id, user_id=omar.id, role="Tech lead"), Activity(**stamp(maya), pursuit_id=pursuit.id, company_id=company.id, contact_id=contact.id, activity_type="Meeting", subject="Discovery and priorities discussion", notes="Aligned on outcomes and next steps.")])
        lead_pursuit = Pursuit(**stamp(maya), name="AI readiness assessment", company_id=company.id, owner_id=maya.id, sourced_by_id=maya.id, holder_id=maya.id, source_channel="LinkedIn", next_action="Confirm the business need", action_type="Call", action_date=date.today() + timedelta(days=3))
        db.add(lead_pursuit); db.flush(); db.add(Lead(**stamp(maya), pursuit_id=lead_pursuit.id, status="working", area_of_interest="AI readiness assessment")); db.commit()
        print("Synthetic FastAPI demo data seeded. Password comes from DEMO_PASSWORD.")


if __name__ == "__main__":
    seed()
