import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from .constants import PROBABILITIES, REFERENCE_DEFAULTS, SERVICES, SOURCES
from .database import engine
from .models import Activity, Artifact, ArtifactRecipient, CommercialSetting, Company, Contact, ExchangeRate, Lead, Opportunity, PartnerInvolvement, PreSalesRequest, Pursuit, PursuitContact, TeamRole, Tenant, User, ValueHistory, WorkingCalendar, WorkspaceReference
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
        now = datetime.now(timezone.utc); today = date.today()

        def company(name, country, domain, industry, owner, company_type="Prospect"):
            item = Company(**stamp(owner), name=name, country=country, domain=domain, industry=industry, company_type=company_type, owner_id=owner.id)
            db.add(item); db.flush(); return item

        def contact(account, first, last, email, title, owner, source="LinkedIn"):
            item = Contact(**stamp(owner), company_id=account.id, first_name=first, last_name=last, email=email, country=account.country, city="", job_title=title, seniority="C-level" if title.startswith("Chief") else "VP or Head", owner_id=owner.id, sourced_by_id=owner.id, source_channel=source, source_detail="Synthetic client-demo relationship", engagement_status="Engaged", consent_basis="Business card or event")
            db.add(item); db.flush(); return item

        northstar = company("Northstar Industries", "United States", "northstar.example", "Manufacturing", maya)
        meridian = company("Meridian Health Group", "United Kingdom", "meridian-health.example", "Healthcare", alex)
        gulf = company("Gulf Horizon Logistics", "United Arab Emirates", "gulf-horizon.example", "Logistics", maya)
        apex = company("Apex Retail Holdings", "India", "apex-retail.example", "Retail", alex)
        alpine = company("Alpine Energy Systems", "Germany", "alpine-energy.example", "Energy", maya)
        partner_company = company("Crescent Technology Partners", "United Arab Emirates", "crescent-partners.example", "Technology", alex, "Referral partner")
        elena = contact(northstar, "Elena", "Rodriguez", "elena@northstar.example", "Chief Digital Officer", maya)
        amelia = contact(meridian, "Amelia", "Clarke", "amelia@meridian-health.example", "Chief Data Officer", alex, "Referral from client")
        khalid = contact(gulf, "Khalid", "Mansoor", "khalid@gulf-horizon.example", "VP Operations", maya, "Exhibition or event")
        priya = contact(apex, "Priya", "Nair", "priya@apex-retail.example", "Chief Technology Officer", alex, "Inbound website enquiry")
        hannah = contact(alpine, "Hannah", "Vogel", "hannah@alpine-energy.example", "Head of Analytics", maya, "Webinar")
        samir = contact(partner_company, "Samir", "Aziz", "samir@crescent-partners.example", "Managing Director", alex, "Referral from partner")

        def opportunity(name, account, primary, owner, holder, stage, service, amount, currency="USD", rate="1", probability=None, close_days=45, source="LinkedIn", created_days=60, restricted=False, blocker="None"):
            created = now - timedelta(days=created_days)
            pursuit = Pursuit(**stamp(owner), name=name, company_id=account.id, owner_id=owner.id, sourced_by_id=owner.id, holder_id=holder.id, source_channel=source, source_detail="Synthetic showcase scenario", next_action="Confirm the next commercial step", action_type="Follow up", action_date=today + timedelta(days=3), priority="High" if stage in {"proposal", "negotiation", "contract"} else "Medium", blocker=blocker, blocker_owner_id=holder.id if blocker != "None" else None, blocked_since=now - timedelta(days=9) if blocker != "None" else None, resolution_action="Agree owner and resolution date" if blocker != "None" else "", created_at=created, first_contacted_at=created + timedelta(days=3), ready_at=created + timedelta(days=8), validated_at=created + timedelta(days=12), presales_assigned_at=created + timedelta(days=18) if stage not in {"discovery"} else None, proposal_sent_at=created + timedelta(days=30) if stage in {"proposal", "negotiation", "contract", "won", "lost"} else None, closed_at=created + timedelta(days=50) if stage in {"won", "lost"} else None, last_client_interaction=now - timedelta(days=4))
            db.add(pursuit); db.flush()
            lead = Lead(**stamp(owner), pursuit_id=pursuit.id, status="closed", outcome="Converted", area_of_interest=service)
            db.add(lead); db.flush()
            value = Decimal(str(amount)); fx = Decimal(str(rate))
            item = Opportunity(**stamp(owner), pursuit_id=pursuit.id, origin_lead_id=lead.id, stage=stage, opportunity_type="Existing client expansion" if account is northstar and name != "Predictive maintenance platform" else "New logo", customer_need=f"Deliver measurable outcomes for {account.name}", scope_summary=f"Discovery, pilot and governed rollout for {name}", primary_contact_id=primary.id, service_line=service, engagement_type="Fixed price", current_value=value, currency=currency, fx_rate=fx, value_usd=value * fx, expected_close_date=today + timedelta(days=close_days), probability=probability if probability is not None else PROBABILITIES[stage], probability_stage_default=PROBABILITIES[stage], restricted=restricted, restriction_reason="Executive commercial negotiation" if restricted else "", gross_margin_pct=Decimal("38"))
            if stage == "won": item.contract_number=f"DEMO-{created_days}-W"; item.contract_date=pursuit.closed_at.date(); item.project_start=today + timedelta(days=14); item.duration_months=6; item.approval_recorded=True; item.approval_note="Synthetic leadership approval"; item.handoff_notes="Kick-off owner and delivery outcomes agreed."
            if stage == "lost": item.loss_reason="Lost to competitor"; item.competitor_name="Example competitor"; item.competitor_status="Known competitor"; item.close_notes="Synthetic loss used for reporting demonstration."
            db.add(item); db.flush()
            db.add_all([ValueHistory(**stamp(owner), opportunity_id=item.id, value_type="Initial estimate", amount=value * Decimal("1.10") if stage == "won" else value, currency=currency, fx_rate=fx), PursuitContact(**stamp(owner), pursuit_id=pursuit.id, contact_id=primary.id, role="Champion"), Activity(**stamp(owner), pursuit_id=pursuit.id, company_id=account.id, contact_id=primary.id, activity_type="Meeting", direction="Outbound", subject=f"{name} discovery and priorities", notes="Synthetic meeting with agreed outcomes and next steps.", activity_date=created + timedelta(days=3))])
            if stage == "won": db.add(ValueHistory(**stamp(owner), opportunity_id=item.id, value_type="Final contract value", amount=value, currency=currency, fx_rate=fx, note="Synthetic signed value"))
            return pursuit, item

        predictive, predictive_opp = opportunity("Predictive maintenance platform", northstar, elena, maya, alex, "proposal", SERVICES[1], "185000", close_days=30, created_days=55)
        db.add_all([TeamRole(**stamp(alex), pursuit_id=predictive.id, user_id=james.id, role="Pre-sales owner"), TeamRole(**stamp(alex), pursuit_id=predictive.id, user_id=omar.id, role="Tech lead")])
        discovery, discovery_opp = opportunity("Clinical data foundation", meridian, amelia, alex, maya, "discovery", SERVICES[3], "95000", close_days=75, source="Referral from client", created_days=24)
        solution, solution_opp = opportunity("Customer intelligence agents", apex, priya, alex, james, "presales", SERVICES[2], "140000", close_days=50, source="Inbound website enquiry", created_days=42, blocker="Technical")
        negotiation_currency = "USD" if settings.instance_type == "US" else "AED"; negotiation_rate = "1" if settings.instance_type == "US" else rates["AED"]
        negotiation, negotiation_opp = opportunity("Fleet optimization program", gulf, khalid, maya, alex, "negotiation", SERVICES[1], "420000", negotiation_currency, negotiation_rate, 65, 20, "Exhibition or event", 78, True, "Legal")
        hold, hold_opp = opportunity("Energy forecasting modernization", alpine, hannah, maya, maya, "hold", SERVICES[0], "80000", close_days=120, source="Webinar", created_days=110, blocker="Budget")
        won, won_opp = opportunity("Operations control tower", northstar, elena, maya, omar, "won", SERVICES[4], "210000", close_days=-20, source="Existing client expansion", created_days=95)
        lost, lost_opp = opportunity("Data quality acceleration", meridian, amelia, alex, alex, "lost", SERVICES[3], "65000", close_days=-12, source="Outbound email", created_days=70)
        deliverable = Artifact(**stamp(maya), pursuit_id=won.id, company_id=northstar.id, title="Operations control tower workshop output", artifact_type="Deck", kind="SharePoint / OneDrive link", storage_link="https://example.invalid/atplcrm-demo/workshop-output", is_reusable=True, approved_by_id=alex.id, approved_at=now - timedelta(days=32), shared_with_client=True, shared_at=now - timedelta(days=30))
        db.add(deliverable); db.flush(); db.add(ArtifactRecipient(**stamp(maya), artifact_id=deliverable.id, contact_id=elena.id))
        won_opp.final_evidence_artifact_id = deliverable.id
        db.add_all([
            PartnerInvolvement(**stamp(maya), opportunity_id=negotiation_opp.id, company_id=partner_company.id, contact_id=samir.id, role="Referral partner", introduced=True, fee_basis="Commission", share_pct=Decimal("10"), applies_to="This contract only", status="Verbally agreed", terms_notes="Synthetic terms awaiting written evidence"),
            PreSalesRequest(**stamp(alex), opportunity_id=solution_opp.id, title="Solution architecture and demo", request_type="Demo", requested_by_id=alex.id, assigned_to_id=omar.id, status="In progress", needed_by=today + timedelta(days=8), estimated_days=Decimal("3"), notes="Showcase active pre-sales request"),
            PreSalesRequest(**stamp(maya), opportunity_id=won_opp.id, title="Executive value workshop", request_type="Workshop", requested_by_id=maya.id, assigned_to_id=omar.id, status="Delivered", needed_by=today - timedelta(days=30), estimated_days=Decimal("2"), actual_days=Decimal("2.5"), deliverable_artifact_id=deliverable.id, approved_by_id=alex.id, accepted_at=now - timedelta(days=40), review_ready_at=now - timedelta(days=34), approved_at=now - timedelta(days=32), delivered_at=now - timedelta(days=30), review_note="Synthetic approval evidence", notes="Showcase delivered pre-sales work"),
        ])

        def open_lead(name, account, primary, owner, status, source, days, outcome="", reason=""):
            created = now - timedelta(days=days)
            pursuit = Pursuit(**stamp(owner), name=name, company_id=account.id, owner_id=owner.id, sourced_by_id=owner.id, holder_id=owner.id, source_channel=source, source_detail="Synthetic lead scenario", next_action="Qualify the customer need", action_type="Call", action_date=today + timedelta(days=4), priority="Medium", created_at=created, first_contacted_at=created + timedelta(days=2) if status != "new" else None, ready_at=created + timedelta(days=7) if status in {"ready", "closed"} else None, last_client_interaction=created + timedelta(days=4) if status in {"engaged", "ready", "closed"} else None)
            db.add(pursuit); db.flush(); db.add(Lead(**stamp(owner), pursuit_id=pursuit.id, status=status, outcome=outcome, reason=reason, area_of_interest=name, revisit_date=today + timedelta(days=60) if outcome == "Nurture" else None))
            if status != "new": db.add(Activity(**stamp(owner), pursuit_id=pursuit.id, company_id=account.id, contact_id=primary.id, activity_type="Call", direction="Outbound", subject=f"Initial discussion: {name}", notes="Synthetic lead activity", activity_date=created + timedelta(days=2)))

        open_lead("AI readiness assessment", northstar, elena, maya, "working", "LinkedIn", 12)
        open_lead("Executive AI workshop", meridian, amelia, alex, "new", "Webinar", 3)
        open_lead("Retail demand forecasting", apex, priya, maya, "engaged", "Marketing campaign", 18)
        open_lead("Data governance advisory", gulf, khalid, alex, "ready", "Referral from partner", 22)
        open_lead("Managed analytics service", alpine, hannah, maya, "closed", "Outbound call", 35, "Nurture", "Budget cycle starts next quarter")
        open_lead("Legacy platform replacement", meridian, amelia, alex, "closed", "Outbound email", 28, "Disqualified", "No genuine requirement")
        db.commit()
        print("Synthetic FastAPI demo data seeded. Password comes from DEMO_PASSWORD.")


if __name__ == "__main__":
    seed()
