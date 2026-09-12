import hashlib
import hmac
import secrets
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from . import presenters as out
from .constants import MANAGEMENT
from .database import get_db
from .models import Activity, AppSession, Artifact, AuditEvent, Company, Contact, ExchangeRate, Lead, Notification, Opportunity, PreSalesRequest, Pursuit, PursuitAction, PursuitContact, TeamRole, User, ValueHistory, WorkspaceReference
from .references import contract as reference_contract, probability as stage_probability, require_code
from .schemas import ActivityInput, ArtifactInput, CompanyInput, CompanyPatch, ContactInput, ContactPatch, ConversionInput, DisqualifyInput, LeadInput, LeadStatusInput, LoginInput, NurtureInput, ProbabilityInput, RequestInput, RequestPatch, RestrictionInput, StageInput, TeamInput, ValueInput, WorkInput
from .security import current_user, delete_session, hash_token, new_session, set_session_cookie, verify_password
from .services import audit, can_value, can_work, future_date, get_scoped, http_error, money, record_value, require_work, scoped, stamp, utc
from .settings import Settings, get_settings

router = APIRouter(prefix="/api/v1")


def user_options() -> tuple:
    return (selectinload(Pursuit.company), selectinload(Pursuit.owner), selectinload(Pursuit.sourced_by), selectinload(Pursuit.holder), selectinload(Pursuit.blocker_owner), selectinload(Pursuit.lead), selectinload(Pursuit.opportunity).selectinload(Opportunity.primary_contact), selectinload(Pursuit.opportunity).selectinload(Opportunity.values), selectinload(Pursuit.opportunity).selectinload(Opportunity.partners), selectinload(Pursuit.team).selectinload(TeamRole.user), selectinload(Pursuit.stakeholders).selectinload(PursuitContact.contact))


def load_pursuit(db: Session, user: User, identifier: UUID, *, lock: bool = False) -> Pursuit:
    statement = scoped(db, Pursuit, user).where(Pursuit.id == identifier).options(*user_options())
    if lock and db.bind and db.bind.dialect.name != "sqlite":
        statement = statement.with_for_update()
    item = db.scalar(statement)
    if not item:
        raise http_error(404, "Record not found.")
    return item


def load_opportunity(db: Session, user: User, identifier: UUID, *, lock: bool = False) -> Opportunity:
    statement = scoped(db, Opportunity, user).where(Opportunity.id == identifier).options(selectinload(Opportunity.pursuit).options(*user_options()), selectinload(Opportunity.primary_contact), selectinload(Opportunity.values), selectinload(Opportunity.partners))
    if lock and db.bind and db.bind.dialect.name != "sqlite":
        statement = statement.with_for_update()
    item = db.scalar(statement)
    if not item:
        raise http_error(404, "Record not found.")
    return item


def tenant_user(db: Session, user: User, identifier: int) -> User:
    item = db.scalar(select(User).where(User.id == identifier, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if not item:
        raise http_error(422, {"user": "Select an active user from this workspace."})
    return item


@router.get("/session/")
def session_info(request: Request, response: Response, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    csrf = secrets.token_urlsafe(32)
    response.set_cookie(settings.csrf_cookie, csrf, max_age=900, httponly=True, secure=settings.app_mode != "local-demo", samesite="lax", path="/")
    user = None
    token = request.cookies.get(settings.session_cookie)
    if token:
        app_session = db.scalar(select(AppSession).where(AppSession.token_hash == hash_token(token)))
        if app_session and utc(app_session.expires_at) > datetime.now(timezone.utc):
            user = db.scalar(select(User).where(User.id == app_session.user_id, User.is_active.is_(True)).options(selectinload(User.tenant)))
            csrf = app_session.csrf_token
            response.set_cookie(settings.csrf_cookie, csrf, max_age=settings.session_hours * 3600, httponly=True, secure=settings.app_mode != "local-demo", samesite="lax", path="/")
    return {"csrf": csrf, "user": out.person(user) if user else None, "mode": settings.app_mode, "instance": settings.instance_type}


@router.post("/session/")
def login(payload: LoginInput, request: Request, response: Response, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if settings.app_mode != "local-demo":
        raise http_error(503, "Connected identity is not configured in this foundation release.")
    supplied = request.headers.get("X-CSRFToken", "")
    cookie = request.cookies.get(settings.csrf_cookie, "")
    if not cookie or not hmac.compare_digest(supplied, cookie):
        raise http_error(403, "CSRF validation failed.")
    user = db.scalar(select(User).where(func.lower(User.username) == str(payload.username).lower(), User.is_active.is_(True)).options(selectinload(User.tenant)))
    if not user or not user.tenant or user.tenant.key != settings.tenant_key or not verify_password(payload.password, user.password):
        raise http_error(400, "Check your email and password.")
    token, app_session = new_session(db, user, settings)
    set_session_cookie(response, token, settings)
    response.set_cookie(settings.csrf_cookie, app_session.csrf_token, max_age=settings.session_hours * 3600, httponly=True, secure=settings.app_mode != "local-demo", samesite="lax", path="/")
    return {"user": out.person(user), "csrf": app_session.csrf_token}


@router.delete("/session/")
def logout(request: Request, response: Response, db: Session = Depends(get_db), settings: Settings = Depends(get_settings), user: User = Depends(current_user)):
    delete_session(request, response, db, settings)
    response.delete_cookie(settings.csrf_cookie, path="/")
    return {"detail": "Signed out."}


@router.get("/bootstrap/")
def bootstrap(db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings)):
    users = db.scalars(select(User).where(User.tenant_id == user.tenant_id, User.is_active.is_(True)).order_by(User.first_name)).all()
    companies = db.scalars(scoped(db, Company, user).options(selectinload(Company.owner)).order_by(Company.name)).all()
    contacts = db.scalars(scoped(db, Contact, user).options(selectinload(Contact.company), selectinload(Contact.owner)).order_by(Contact.first_name, Contact.last_name)).all()
    pursuits = db.scalars(scoped(db, Pursuit, user).options(*user_options())).unique().all()
    leads = [item.lead for item in pursuits if item.lead]
    opportunities = [item.opportunity for item in pursuits if item.opportunity]
    requests = db.scalars(scoped(db, PreSalesRequest, user).options(selectinload(PreSalesRequest.assigned_to), selectinload(PreSalesRequest.opportunity).selectinload(Opportunity.pursuit))).all()
    activity_rows = db.scalars(scoped(db, Activity, user).options(selectinload(Activity.company), selectinload(Activity.created_by), selectinload(Activity.pursuit).selectinload(Pursuit.opportunity)).order_by(Activity.activity_date.desc()).limit(100)).all()
    activities = [item for item in activity_rows if not item.pursuit or not item.pursuit.opportunity or can_value(db, user, item.pursuit.opportunity)][:50]
    notifications = db.scalars(scoped(db, Notification, user).where(Notification.recipient_id == user.id).order_by(Notification.created_at.desc()).limit(50)).all()
    rates = db.scalars(scoped(db, ExchangeRate, user).order_by(ExchangeRate.currency)).all()
    references = reference_contract(db, user); references["currencies"] = [{"id": str(item.id), "currency": item.currency, "rate": str(item.rate), "source": item.source} for item in rates]
    admin_users = db.scalars(select(User).where(User.tenant_id == user.tenant_id).order_by(User.is_active.desc(), User.first_name, User.last_name)).all() if user.level == "Administrator" else []
    admin_references = db.scalars(scoped(db, WorkspaceReference, user).order_by(WorkspaceReference.category, WorkspaceReference.sort_order, WorkspaceReference.label)).all() if user.level == "Administrator" else []
    return {"user": out.person(user), "instance": settings.instance_type, "mode": settings.app_mode, "today": date.today(), "users": [out.person(item) for item in users], "admin_users": [out.person(item) for item in admin_users], "admin_references": [{"id": str(item.id), "category": item.category, "code": item.code, "label": item.label, "numeric_value": item.numeric_value, "sort_order": item.sort_order, "active": item.active} for item in admin_references], "companies": [out.company(item) for item in companies], "contacts": [out.contact(db, item) for item in contacts], "leads": [out.lead(db, item, user) for item in leads], "opportunities": [out.opportunity(db, item, user) for item in opportunities], "requests": [out.request(item) for item in requests], "activities": [out.activity(item) for item in activities], "notifications": [{"id": str(item.id), "message": item.message, "category": item.category, "severity": item.severity, "read": item.read, "read_at": item.read_at, "pursuit_id": str(item.pursuit_id) if item.pursuit_id else None, "created_at": item.created_at} for item in notifications], "reference": references}


@router.post("/companies/", status_code=201)
def create_company(payload: CompanyInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if db.scalar(scoped(db, Company, user).where(func.lower(Company.name) == payload.name.lower())):
        raise http_error(422, {"name": "A company with this name already exists. Use the existing company."})
    owner = tenant_user(db, user, payload.owner)
    item = Company(**stamp(user), **payload.model_dump(exclude={"owner"}), owner_id=owner.id)
    db.add(item); audit(db, user, "Company created", detail=item.name); db.commit(); db.refresh(item)
    item.owner = owner
    return out.company(item)


@router.patch("/companies/{identifier}/")
def update_company(identifier: UUID, payload: CompanyPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = get_scoped(db, Company, user, identifier)
    if item.owner_id != user.id and user.level not in MANAGEMENT:
        raise http_error(403, "Only the relationship owner or management can edit this company.")
    values = payload.model_dump(exclude_unset=True)
    if "owner" in values:
        values["owner_id"] = tenant_user(db, user, values.pop("owner")).id
    for key, value in values.items(): setattr(item, key, value)
    item.updated_by_id = user.id; audit(db, user, "Company updated", detail=item.name); db.commit(); db.refresh(item)
    item.owner = tenant_user(db, user, item.owner_id)
    return out.company(item)


@router.post("/contacts/", status_code=201)
def create_contact(payload: ContactInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    company = get_scoped(db, Company, user, payload.company); owner = tenant_user(db, user, payload.owner)
    email = str(payload.email).lower()
    if email and db.scalar(scoped(db, Contact, user).where(func.lower(Contact.email) == email)):
        raise http_error(422, {"email": "This email already exists. Open the existing contact instead."})
    values = payload.model_dump(exclude={"company", "owner"}); values["email"] = email
    item = Contact(**stamp(user), **values, company_id=company.id, owner_id=owner.id, sourced_by_id=user.id)
    db.add(item); audit(db, user, "Contact created", detail=item.name); db.commit(); db.refresh(item)
    item.company, item.owner = company, owner
    return out.contact(db, item)


@router.patch("/contacts/{identifier}/")
def update_contact(identifier: UUID, payload: ContactPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = get_scoped(db, Contact, user, identifier)
    if item.owner_id != user.id and user.level not in MANAGEMENT:
        raise http_error(403, "Only the relationship owner or management can edit this contact.")
    values = payload.model_dump(exclude_unset=True)
    if "company" in values: values["company_id"] = get_scoped(db, Company, user, values.pop("company")).id
    if "owner" in values: values["owner_id"] = tenant_user(db, user, values.pop("owner")).id
    if values.get("email"):
        duplicate = db.scalar(scoped(db, Contact, user).where(func.lower(Contact.email) == str(values["email"]).lower(), Contact.id != item.id))
        if duplicate: raise http_error(422, {"email": "This email already exists."})
        values["email"] = str(values["email"]).lower()
    for key, value in values.items(): setattr(item, key, value)
    item.updated_by_id = user.id; audit(db, user, "Contact updated", detail=item.name); db.commit(); db.refresh(item)
    item.company = get_scoped(db, Company, user, item.company_id); item.owner = tenant_user(db, user, item.owner_id)
    return out.contact(db, item)


@router.post("/leads/", status_code=201)
def create_lead(payload: LeadInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    future_date(payload.action_date)
    require_code(db, user, "actions", payload.action_type, "action_type"); require_code(db, user, "sources", payload.source_channel, "source_channel")
    company = get_scoped(db, Company, user, payload.company); owner = tenant_user(db, user, payload.owner); holder = tenant_user(db, user, payload.holder)
    pursuit = Pursuit(**stamp(user), name=payload.name, company_id=company.id, owner_id=owner.id, sourced_by_id=user.id, holder_id=holder.id, next_action=payload.next_action, action_type=payload.action_type, action_date=payload.action_date, source_channel=payload.source_channel, source_detail=payload.source_detail, priority=payload.priority)
    db.add(pursuit); db.flush()
    lead = Lead(**stamp(user), pursuit_id=pursuit.id, area_of_interest=payload.area_of_interest)
    db.add(lead); audit(db, user, "Lead created", pursuit, "Prospecting is separate from the commercial pipeline."); db.commit()
    pursuit = load_pursuit(db, user, pursuit.id)
    return out.lead(db, pursuit.lead, user)


def lead_record(db: Session, user: User, identifier: UUID) -> Lead:
    lead = db.scalar(scoped(db, Lead, user).where(Lead.id == identifier).options(selectinload(Lead.pursuit).options(*user_options())))
    if not lead: raise http_error(404, "Record not found.")
    return lead


@router.post("/leads/{identifier}/status/")
def update_lead_status(identifier: UUID, payload: LeadStatusInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = lead_record(db, user, identifier); require_work(db, user, lead.pursuit)
    if lead.outcome == "Converted": raise http_error(422, "This lead has been converted. Work its linked opportunity.")
    lead.status, lead.outcome, lead.reason, lead.revisit_date = payload.status, "", "", None
    if payload.status == "ready" and not lead.pursuit.ready_at: lead.pursuit.ready_at = datetime.now(timezone.utc)
    lead.pursuit.version += 1; audit(db, user, "Lead status", lead.pursuit, payload.status); db.commit()
    return out.lead(db, load_pursuit(db, user, lead.pursuit_id).lead, user)


@router.post("/leads/{identifier}/disqualify/")
def disqualify_lead(identifier: UUID, payload: DisqualifyInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = lead_record(db, user, identifier); pursuit = lead.pursuit
    if user.level not in {"Manager", "Executive"} or user.id in {pursuit.sourced_by_id, pursuit.owner_id}: raise http_error(403, "An independent Manager or Executive must disqualify this lead.")
    require_code(db, user, "disqualification_reasons", payload.reason, "reason")
    lead.status, lead.outcome, lead.reason = "closed", "Disqualified", payload.reason; pursuit.version += 1; audit(db, user, "Lead disqualified", pursuit, payload.reason); db.commit()
    return out.lead(db, load_pursuit(db, user, pursuit.id).lead, user)


@router.post("/leads/{identifier}/nurture/")
def nurture_lead(identifier: UUID, payload: NurtureInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = lead_record(db, user, identifier); require_work(db, user, lead.pursuit); future_date(payload.revisit_date, "revisit_date")
    lead.status, lead.outcome, lead.revisit_date = "closed", "Nurture", payload.revisit_date; lead.pursuit.version += 1; audit(db, user, "Lead nurtured", lead.pursuit, str(payload.revisit_date)); db.commit()
    return out.lead(db, load_pursuit(db, user, lead.pursuit_id).lead, user)


@router.post("/leads/{identifier}/convert/")
def convert_lead(identifier: UUID, payload: ConversionInput, db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings)):
    lead = lead_record(db, user, identifier); pursuit = lead.pursuit
    if user.level not in {"Manager", "Executive"}: raise http_error(403, "A Manager or Executive must validate this lead.")
    if user.id in {pursuit.sourced_by_id, pursuit.owner_id}: raise http_error(403, "Self-validation is not allowed. Ask an independent Manager or Executive.")
    if lead.converted_opportunity: return out.opportunity(db, lead.converted_opportunity, user)
    if lead.status != "ready": raise http_error(422, "Submit the lead for validation first.")
    require_code(db, user, "services", payload.service_line, "service_line")
    rate = db.scalar(scoped(db, ExchangeRate, user).where(ExchangeRate.currency == payload.currency))
    if not rate or (settings.instance_type == "US" and payload.currency != "USD"): raise http_error(422, {"currency": "No permitted reference rate for this currency."})
    contact = get_scoped(db, Contact, user, payload.primary_contact)
    if contact.company_id != pursuit.company_id: raise http_error(422, {"primary_contact": "Choose a contact at this client company."})
    opportunity = Opportunity(**stamp(user), pursuit_id=pursuit.id, origin_lead_id=lead.id, customer_need=payload.customer_need, scope_summary=payload.scope_summary, primary_contact_id=contact.id, current_value=payload.current_value, currency=payload.currency, fx_rate=rate.rate, value_usd=money(payload.current_value * rate.rate), service_line=payload.service_line, expected_close_date=payload.expected_close_date, opportunity_type=payload.opportunity_type, engagement_type=payload.engagement_type, probability=20)
    db.add(opportunity); db.flush(); db.add(ValueHistory(**stamp(user), opportunity_id=opportunity.id, value_type="Initial estimate", amount=payload.current_value, currency=payload.currency, fx_rate=rate.rate))
    existing = db.scalar(scoped(db, PursuitContact, user).where(PursuitContact.pursuit_id == pursuit.id, PursuitContact.contact_id == contact.id))
    if not existing: db.add(PursuitContact(**stamp(user), pursuit_id=pursuit.id, contact_id=contact.id, role="Champion"))
    lead.status, lead.outcome = "closed", "Converted"; pursuit.validated_at = datetime.now(timezone.utc); pursuit.version += 1
    audit(db, user, "Lead validated and converted", pursuit, "Original contacts, team, source and timeline preserved.", after={"opportunity_id": str(opportunity.id)}); db.commit()
    return out.opportunity(db, load_opportunity(db, user, opportunity.id), user)


@router.patch("/pursuits/{identifier}/")
def update_work(identifier: UUID, payload: WorkInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, identifier, lock=True); require_work(db, user, pursuit)
    if payload.version != pursuit.version: raise http_error(409, "This pursuit changed. Refresh before saving.")
    values = payload.model_dump(exclude_unset=True, exclude={"version", "reason"})
    if values.get("action_type") is not None: require_code(db, user, "actions", values["action_type"], "action_type")
    if values.get("blocker") is not None: require_code(db, user, "blockers", values["blocker"], "blocker")
    if "holder" in values:
        values["holder_id"] = tenant_user(db, user, values.pop("holder")).id
    if "blocker_owner" in values:
        values["blocker_owner_id"] = tenant_user(db, user, values.pop("blocker_owner")).id if values["blocker_owner"] else None
    handoff = "holder_id" in values and values["holder_id"] != pursuit.holder_id
    action_changed = any(key in values and values[key] != getattr(pursuit, key) for key in ("next_action", "action_type", "action_date"))
    if handoff or action_changed:
        for field in ("next_action", "action_type", "action_date"):
            if field not in values: raise http_error(422, {field: "Provide the complete next action when changing it or handing off."})
        future_date(values["action_date"])
    before = {"holder": pursuit.holder_id, "action": pursuit.next_action, "date": str(pursuit.action_date), "blocker": pursuit.blocker}
    if handoff: pursuit.ball_since = datetime.now(timezone.utc)
    blocker = values.get("blocker", pursuit.blocker)
    blocker_owner = values.get("blocker_owner_id", pursuit.blocker_owner_id)
    resolution = values.get("resolution_action", pursuit.resolution_action)
    if blocker != "None":
        if not blocker_owner or not resolution: raise http_error(422, "A blocker needs an owner and a resolution action.")
        if blocker != pursuit.blocker: pursuit.blocked_since = datetime.now(timezone.utc)
    else:
        values.update(blocker_owner_id=None, resolution_action=""); pursuit.blocked_since = None
    for key, value in values.items(): setattr(pursuit, key, value)
    pursuit.version += 1; pursuit.updated_by_id = user.id
    audit(db, user, "Responsibility handed over" if handoff else "Next action / blocker updated", pursuit, payload.reason, before=before, after={"holder": pursuit.holder_id, "action": pursuit.next_action, "date": str(pursuit.action_date), "blocker": pursuit.blocker}); db.commit()
    return out.pursuit(db, load_pursuit(db, user, identifier), user)


@router.post("/opportunities/{identifier}/stage/")
def update_stage(identifier: UUID, payload: StageInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, identifier, lock=True)
    pursuit = load_pursuit(db, user, opportunity.pursuit_id, lock=True)
    opportunity.pursuit = pursuit
    require_work(db, user, pursuit)
    if payload.version != pursuit.version: raise http_error(409, "This pursuit changed. Refresh before moving it.")
    require_code(db, user, "stages", payload.stage, "stage")
    if payload.stage == opportunity.stage:
        return out.opportunity(db, opportunity, user)
    if payload.stage in {"presales", "proposal", "negotiation", "contract", "won"}:
        roles = set(db.scalars(scoped(db, TeamRole, user).where(TeamRole.pursuit_id == pursuit.id, TeamRole.role.in_(["Pre-sales owner", "Tech lead"]))).all())
        role_names = {role.role for role in roles}
        if role_names != {"Pre-sales owner", "Tech lead"}: raise http_error(422, "Assign a pre-sales owner and tech lead first.")
    if payload.stage == "hold":
        if not payload.revisit_date: raise http_error(422, {"revisit_date": "A future revisit date is required."})
        opportunity.revisit_date = future_date(payload.revisit_date, "revisit_date")
    if payload.stage == "lost":
        if not payload.loss_reason: raise http_error(422, {"loss_reason": "Choose a loss reason."})
        require_code(db, user, "loss_reasons", payload.loss_reason, "loss_reason")
        opportunity.loss_reason, opportunity.competitor_name = payload.loss_reason, payload.competitor_name
    if payload.stage == "won":
        if not can_value(db, user, opportunity): raise http_error(403, "Value access is required to close this deal.")
        if not payload.contract_number or not payload.contract_date or payload.final_value is None: raise http_error(422, "Contract number, date and final value are required.")
        evidence = db.scalar(scoped(db, Artifact, user).where(Artifact.pursuit_id == pursuit.id, Artifact.artifact_type.in_(["Contract", "Purchase order", "SOW"])))
        if not evidence: raise http_error(422, "Register the final Contract, Purchase order or SOW evidence link first.")
        opportunity.contract_number, opportunity.contract_date = payload.contract_number, payload.contract_date
        record_value(db, user, opportunity, payload.final_value, "Final contract value")
    old = opportunity.stage; opportunity.stage = payload.stage; opportunity.probability = stage_probability(db, user, payload.stage); opportunity.probability_note = ""
    now = datetime.now(timezone.utc)
    if payload.stage == "presales" and not pursuit.presales_assigned_at: pursuit.presales_assigned_at = now
    if payload.stage == "proposal" and not pursuit.proposal_sent_at: pursuit.proposal_sent_at = now
    if payload.stage in {"won", "lost"}: pursuit.closed_at = now
    old_version = pursuit.version; pursuit.version += 1
    audit(db, user, "Stage changed", pursuit, payload.reason, before={"stage": old, "version": old_version}, after={"stage": payload.stage, "version": pursuit.version}); db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/opportunities/{identifier}/value/")
def update_value(identifier: UUID, payload: ValueInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, identifier); pursuit = opportunity.pursuit
    if not can_value(db, user, opportunity) or (user.id != pursuit.owner_id and user.level not in MANAGEMENT): raise http_error(403, "Only the commercial owner or management can update value.")
    if payload.value_type not in {"Initial estimate", "Proposal value", "Revised proposal", "Negotiated value", "Final contract value"}: raise http_error(422, {"value_type": "Choose a valid value type."})
    previous = str(opportunity.current_value); record_value(db, user, opportunity, payload.amount, payload.value_type, payload.note); audit(db, user, "Value recorded", pursuit, payload.value_type, before={"amount": previous}, after={"amount": str(payload.amount)}); db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/opportunities/{identifier}/restriction/")
def update_restriction(identifier: UUID, payload: RestrictionInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level not in {"Manager", "Executive"}: raise http_error(403, "A Manager or Executive must change value restrictions.")
    opportunity = load_opportunity(db, user, identifier); opportunity.restricted, opportunity.restriction_reason = payload.restricted, payload.reason; audit(db, user, "Value visibility changed", opportunity.pursuit, payload.reason, after={"restricted": payload.restricted}); db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/opportunities/{identifier}/team/")
def assign_team(identifier: UUID, payload: TeamInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, identifier); pursuit = opportunity.pursuit
    if user.level not in MANAGEMENT and user.id != pursuit.owner_id: raise http_error(403, "Only the commercial owner or management can assign the team.")
    member = tenant_user(db, user, payload.user_id)
    if payload.role != "Supporting contributor":
        existing = db.scalar(scoped(db, TeamRole, user).where(TeamRole.pursuit_id == pursuit.id, TeamRole.role == payload.role))
        if existing: existing.user_id = member.id; existing.updated_by_id = user.id
        else: db.add(TeamRole(**stamp(user), pursuit_id=pursuit.id, user_id=member.id, role=payload.role))
    elif not db.scalar(scoped(db, TeamRole, user).where(TeamRole.pursuit_id == pursuit.id, TeamRole.user_id == member.id, TeamRole.role == payload.role)):
        db.add(TeamRole(**stamp(user), pursuit_id=pursuit.id, user_id=member.id, role=payload.role))
    if payload.role == "Pre-sales owner" and not pursuit.presales_assigned_at:
        pursuit.presales_assigned_at = datetime.now(timezone.utc)
        pursuit.version += 1
    audit(db, user, "Team assigned", pursuit, f"{member.display_name} · {payload.role}"); db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/opportunities/{identifier}/probability/")
def update_probability(identifier: UUID, payload: ProbabilityInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level not in {"Manager", "Executive"}: raise http_error(403, "A Manager or Executive must override probability.")
    opportunity = load_opportunity(db, user, identifier); opportunity.probability, opportunity.probability_note = payload.probability, payload.reason; audit(db, user, "Probability overridden", opportunity.pursuit, payload.reason, after={"probability": payload.probability}); db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/activities/", status_code=201)
def create_activity(payload: ActivityInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    company = get_scoped(db, Company, user, payload.company); pursuit = load_pursuit(db, user, payload.pursuit) if payload.pursuit else None; contact = get_scoped(db, Contact, user, payload.contact) if payload.contact else None
    if pursuit:
        require_work(db, user, pursuit)
        if pursuit.company_id != company.id: raise http_error(422, "The activity company must match the pursuit.")
    if contact and contact.company_id != company.id: raise http_error(422, "The contact must belong to the activity company.")
    client_facing = payload.activity_type != "Internal note"
    if client_facing and not contact: raise http_error(422, {"contact": "Select the client contact for this interaction."})
    if contact and contact.do_not_contact and payload.direction == "Outbound" and client_facing and not payload.override_reason: raise http_error(422, {"override_reason": "This contact is marked Do not contact. An override reason is required."})
    activity_date = payload.activity_date or datetime.now(timezone.utc)
    if utc(activity_date) > datetime.now(timezone.utc): raise http_error(422, {"activity_date": "Log completed interactions only. Schedule future work as a next action."})
    item = Activity(**stamp(user), pursuit_id=pursuit.id if pursuit else None, contact_id=contact.id if contact else None, company_id=company.id, activity_type=payload.activity_type, is_client_facing=client_facing, direction=payload.direction, activity_date=activity_date, outcome=payload.outcome, subject=payload.subject, notes=payload.notes, override_reason=payload.override_reason)
    db.add(item)
    if pursuit and client_facing:
        if not pursuit.last_client_interaction or utc(activity_date) > utc(pursuit.last_client_interaction): pursuit.last_client_interaction = activity_date
        if payload.direction == "Outbound" and (not pursuit.first_contacted_at or utc(activity_date) < utc(pursuit.first_contacted_at)): pursuit.first_contacted_at = activity_date
    warning = None
    if contact and client_facing and payload.direction == "Outbound" and contact.owner_id != user.id:
        warning = f"{contact.owner.display_name} owns this contact and has been notified."
        db.add(Notification(**stamp(user), recipient_id=contact.owner_id, pursuit_id=pursuit.id if pursuit else None, key=f"collision:{item.id}", message=f"{user.display_name} logged outreach to your contact {contact.name}."))
    audit(db, user, "Activity logged", pursuit, payload.activity_type); db.commit(); db.refresh(item); item.company, item.contact, item.pursuit, item.created_by = company, contact, pursuit, user
    return {"activity": out.activity(item), "warning": warning}


@router.get("/pursuits/{identifier}/timeline/")
def timeline(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, identifier); opportunity = pursuit.opportunity; visible = not opportunity or can_value(db, user, opportunity)
    events = db.scalars(scoped(db, AuditEvent, user).where(AuditEvent.pursuit_id == pursuit.id).options(selectinload(AuditEvent.created_by)).order_by(AuditEvent.created_at.desc())).all()
    if not visible:
        events = [event for event in events if event.action not in {"Value recorded", "Exchange rate updated"}]
        return {"activities": [], "events": [{"id": str(event.id), "action": event.action, "detail": "", "date": event.created_at, "author": event.created_by.display_name if event.created_by else "System"} for event in events], "completed_actions": [], "artifacts": [], "restricted_content": True}
    activities = db.scalars(scoped(db, Activity, user).where(Activity.pursuit_id == pursuit.id).options(selectinload(Activity.company), selectinload(Activity.created_by)).order_by(Activity.activity_date.desc())).all()
    artifact_query = scoped(db, Artifact, user).where(Artifact.pursuit_id == pursuit.id)
    if not can_work(db, user, pursuit): artifact_query = artifact_query.where(Artifact.internal_only.is_(False))
    artifacts = db.scalars(artifact_query).all()
    actions = db.scalars(scoped(db, PursuitAction, user).where(PursuitAction.pursuit_id == pursuit.id).options(selectinload(PursuitAction.completed_by)).order_by(PursuitAction.completed_at.desc())).all()
    return {"activities": [out.activity(item) for item in activities], "events": [{"id": str(event.id), "action": event.action, "detail": event.detail, "date": event.created_at, "author": event.created_by.display_name if event.created_by else "System"} for event in events], "completed_actions": [out.completed_action(item) for item in actions], "artifacts": [{"id": str(item.id), "title": item.title, "type": item.artifact_type, "url": item.storage_link, "version": item.version, "internal_only": item.internal_only, "approved": bool(item.approved_by_id), "shared_at": item.shared_at} for item in artifacts]}


@router.post("/requests/", status_code=201)
def create_request(payload: RequestInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, payload.opportunity); require_work(db, user, opportunity.pursuit)
    is_presales_owner = db.scalar(scoped(db, TeamRole, user).where(TeamRole.pursuit_id == opportunity.pursuit_id, TeamRole.user_id == user.id, TeamRole.role == "Pre-sales owner"))
    if user.level not in MANAGEMENT and not is_presales_owner: raise http_error(403, "Management or the pre-sales owner assigns requests.")
    assignee = tenant_user(db, user, payload.assigned_to)
    item = PreSalesRequest(**stamp(user), opportunity_id=opportunity.id, assigned_to_id=assignee.id, **payload.model_dump(exclude={"opportunity", "assigned_to"}))
    db.add(item)
    if not db.scalar(scoped(db, TeamRole, user).where(TeamRole.pursuit_id == opportunity.pursuit_id, TeamRole.user_id == assignee.id, TeamRole.role == "Supporting contributor")):
        db.add(TeamRole(**stamp(user), pursuit_id=opportunity.pursuit_id, user_id=assignee.id, role="Supporting contributor"))
    audit(db, user, "Pre-sales requested", opportunity.pursuit, item.title); db.commit()
    item = db.scalar(scoped(db, PreSalesRequest, user).where(PreSalesRequest.id == item.id).options(selectinload(PreSalesRequest.assigned_to), selectinload(PreSalesRequest.opportunity).selectinload(Opportunity.pursuit)))
    return out.request(item)


@router.patch("/requests/{identifier}/")
def update_request(identifier: UUID, payload: RequestPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(scoped(db, PreSalesRequest, user).where(PreSalesRequest.id == identifier).options(selectinload(PreSalesRequest.opportunity).selectinload(Opportunity.pursuit), selectinload(PreSalesRequest.assigned_to)))
    if not item: raise http_error(404, "Record not found.")
    require_work(db, user, item.opportunity.pursuit)
    if item.assigned_to_id != user.id and user.level not in MANAGEMENT: raise http_error(403, "Only the assignee or management can update this request.")
    require_code(db, user, "request_statuses", payload.status, "status")
    if payload.status == "Approved to share" and user.level not in MANAGEMENT: raise http_error(403, "Manager approval is required.")
    if payload.status == "Delivered":
        if item.status != "Approved to share": raise http_error(422, "Obtain approval before delivery.")
        if payload.actual_days is None: raise http_error(422, {"actual_days": "Actual days are required at delivery."})
        item.actual_days = payload.actual_days
    if payload.status == "Blocked":
        if not payload.blocked_reason: raise http_error(422, {"blocked_reason": "Explain the blocker."})
        item.blocked_reason = payload.blocked_reason
    item.status = payload.status; audit(db, user, "Pre-sales status changed", item.opportunity.pursuit, f"{item.title}: {payload.status}"); db.commit()
    return out.request(item)


@router.post("/artifacts/", status_code=201)
def create_artifact(payload: ArtifactInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, payload.pursuit); require_work(db, user, pursuit)
    item = Artifact(**stamp(user), pursuit_id=pursuit.id, title=payload.title, artifact_type=payload.artifact_type, storage_link=str(payload.storage_link), version=payload.version, internal_only=payload.internal_only)
    db.add(item); audit(db, user, "Evidence registered", pursuit, item.title); db.commit(); return {"id": str(item.id)}
