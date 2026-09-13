from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from . import presenters as out
from .api import load_opportunity
from .constants import MANAGEMENT
from .database import get_db
from .models import (
    Artifact,
    CommercialSetting,
    Company,
    Contact,
    ExchangeRate,
    ExchangeRateHistory,
    Notification,
    Opportunity,
    PartnerInvolvement,
    User,
    ValueHistory,
)
from .schemas import (
    CommercialDetailsInput,
    CommercialSettingsInput,
    OpportunityRateInput,
    PartnerInput,
    RateRefreshInput,
    RebaselineInput,
)
from .security import current_user
from .services import audit, can_value, commercial_totals, get_scoped, http_error, money, scoped, stamp
from .settings import Settings, get_settings

router = APIRouter(prefix="/api/v1", tags=["commercial"])
PARTNER_COMPANY_TYPES = {"Referral partner", "Reseller", "Local partner", "Prime contractor", "Subcontractor"}
OPEN_STAGES = {"discovery", "qualified", "presales", "proposal", "negotiation", "contract", "hold"}
ADVANCED_STAGES = {"proposal", "negotiation", "contract", "won"}


def require_commercial_editor(db: Session, user: User, opportunity: Opportunity) -> None:
    if not can_value(db, user, opportunity) or (user.id != opportunity.pursuit.owner_id and user.level not in MANAGEMENT):
        raise http_error(403, "Only the commercial owner or management can change commercial terms.")


def setting_for(db: Session, user: User) -> CommercialSetting:
    item = db.scalar(scoped(db, CommercialSetting, user))
    if item:
        return item
    item = CommercialSetting(**stamp(user), partner_share_warning_pct=Decimal("40"), fx_movement_notice_pct=Decimal("5"))
    db.add(item); db.flush()
    return item


def setting_out(item: CommercialSetting) -> dict:
    return {"partner_share_warning_pct": str(item.partner_share_warning_pct), "fx_movement_notice_pct": str(item.fx_movement_notice_pct)}


def validate_partner(db: Session, user: User, opportunity: Opportunity, payload: PartnerInput) -> tuple[Company, Contact, Artifact | None]:
    company = get_scoped(db, Company, user, payload.company_id)
    if company.company_type not in PARTNER_COMPANY_TYPES:
        raise http_error(422, {"company_id": "Choose a company whose type is Referral partner, Reseller, Local partner, Prime contractor or Subcontractor."})
    contact = get_scoped(db, Contact, user, payload.contact_id)
    if contact.company_id != company.id:
        raise http_error(422, {"contact_id": "The partner contact must belong to the selected partner company."})
    artifact = None
    if payload.agreement_artifact_id:
        artifact = get_scoped(db, Artifact, user, payload.agreement_artifact_id)
        if artifact.pursuit_id != opportunity.pursuit_id:
            raise http_error(422, {"agreement_artifact_id": "The agreement evidence must belong to this pursuit."})
    if payload.fee_basis == "Percentage of gross margin" and opportunity.gross_margin_pct is None:
        raise http_error(422, {"fee_basis": "Set the opportunity gross-margin percentage before adding margin-based partner terms."})
    return company, contact, artifact


@router.get("/commercial/settings/")
def commercial_settings(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return setting_out(setting_for(db, user))


@router.patch("/commercial/settings/")
def update_commercial_settings(payload: CommercialSettingsInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level != "Administrator":
        raise http_error(403, "Workspace Administrator access is required.")
    item = setting_for(db, user)
    before = setting_out(item)
    item.partner_share_warning_pct = payload.partner_share_warning_pct
    item.fx_movement_notice_pct = payload.fx_movement_notice_pct
    item.updated_by_id = user.id
    audit(db, user, "Commercial settings updated", before=before, after=setting_out(item))
    db.commit()
    return setting_out(item)


@router.patch("/opportunities/{identifier}/commercial/")
def update_commercial_details(identifier: UUID, payload: CommercialDetailsInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, identifier, lock=True)
    require_commercial_editor(db, user, opportunity)
    before = {"gross_margin_pct": str(opportunity.gross_margin_pct) if opportunity.gross_margin_pct is not None else None, "approval_recorded": opportunity.approval_recorded, "approval_note": opportunity.approval_note}
    opportunity.gross_margin_pct = payload.gross_margin_pct
    opportunity.approval_recorded = payload.approval_recorded
    opportunity.approval_note = payload.approval_note
    opportunity.updated_by_id = user.id
    audit(db, user, "Commercial details updated", opportunity.pursuit, payload.approval_note, before=before, after={"gross_margin_pct": str(payload.gross_margin_pct) if payload.gross_margin_pct is not None else None, "approval_recorded": payload.approval_recorded, "approval_note": payload.approval_note})
    db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.post("/opportunities/{identifier}/partners/", status_code=201)
def create_partner(identifier: UUID, payload: PartnerInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    opportunity = load_opportunity(db, user, identifier, lock=True)
    require_commercial_editor(db, user, opportunity)
    company, contact, _artifact = validate_partner(db, user, opportunity, payload)
    item = PartnerInvolvement(**stamp(user), opportunity_id=opportunity.id, **payload.model_dump())
    db.add(item); db.flush()
    audit(db, user, "Partner involvement added", opportunity.pursuit, f"{company.name} · {payload.role}", after={"partner_id": str(item.id), "fee_basis": item.fee_basis, "share_pct": str(item.share_pct), "fixed_fee": str(item.fixed_fee), "status": item.status})
    db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


@router.patch("/partners/{identifier}/")
def update_partner(identifier: UUID, payload: PartnerInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = get_scoped(db, PartnerInvolvement, user, identifier)
    opportunity = load_opportunity(db, user, item.opportunity_id, lock=True)
    require_commercial_editor(db, user, opportunity)
    company, _contact, _artifact = validate_partner(db, user, opportunity, payload)
    before = {"company_id": str(item.company_id), "fee_basis": item.fee_basis, "share_pct": str(item.share_pct), "fixed_fee": str(item.fixed_fee), "status": item.status}
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.updated_by_id = user.id
    audit(db, user, "Partner involvement updated", opportunity.pursuit, company.name, before=before, after={"company_id": str(item.company_id), "fee_basis": item.fee_basis, "share_pct": str(item.share_pct), "fixed_fee": str(item.fixed_fee), "status": item.status})
    db.commit()
    return out.opportunity(db, load_opportunity(db, user, opportunity.id), user)


@router.delete("/partners/{identifier}/", status_code=204)
def delete_partner(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = get_scoped(db, PartnerInvolvement, user, identifier)
    opportunity = load_opportunity(db, user, item.opportunity_id, lock=True)
    require_commercial_editor(db, user, opportunity)
    item.is_deleted = True; item.updated_by_id = user.id
    audit(db, user, "Partner involvement removed", opportunity.pursuit, before={"partner_id": str(item.id), "company_id": str(item.company_id), "fee_basis": item.fee_basis})
    db.commit()


@router.post("/opportunities/{identifier}/rate/")
def update_opportunity_rate(identifier: UUID, payload: OpportunityRateInput, db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings)):
    opportunity = load_opportunity(db, user, identifier, lock=True)
    require_commercial_editor(db, user, opportunity)
    if opportunity.currency == "USD" and payload.rate != 1:
        raise http_error(422, {"rate": "USD is the reporting base and its rate must remain 1."})
    if settings.instance_type == "US" and opportunity.currency != "USD":
        raise http_error(422, "The US deployment supports USD opportunities only.")
    old = opportunity.fx_rate
    opportunity.fx_rate = payload.rate
    opportunity.value_usd = money(opportunity.current_value * payload.rate)
    opportunity.updated_by_id = user.id
    db.add(ValueHistory(**stamp(user), opportunity_id=opportunity.id, value_type="Exchange rate update", amount=opportunity.current_value, currency=opportunity.currency, fx_rate=payload.rate, note=payload.reason))
    audit(db, user, "Opportunity exchange rate updated", opportunity.pursuit, payload.reason, before={"rate": str(old), "value_usd": str(money(opportunity.current_value * old))}, after={"rate": str(payload.rate), "value_usd": str(opportunity.value_usd)})
    db.commit()
    return out.opportunity(db, load_opportunity(db, user, identifier), user)


def apply_rate_refresh(db: Session, actor: User, payload: RateRefreshInput, *, change_type: str = "Published refresh") -> dict:
    settings = setting_for(db, actor)
    updated = 0; notices = []
    for supplied in payload.rates:
        item = db.scalar(scoped(db, ExchangeRate, actor).where(ExchangeRate.currency == supplied.currency))
        if not item:
            continue
        if item.currency == "USD" and supplied.rate != 1:
            raise http_error(422, {"rates": "USD is the reporting base and must remain 1."})
        old = item.rate
        movement = abs((supplied.rate - old) / old * 100) if old else Decimal("0")
        item.rate = supplied.rate; item.source = payload.source; item.effective_date = payload.effective_date; item.updated_by_id = actor.id
        db.add(ExchangeRateHistory(**stamp(actor), currency=item.currency, old_rate=old, new_rate=supplied.rate, source=payload.source, effective_date=payload.effective_date, change_type=change_type))
        if movement > settings.fx_movement_notice_pct:
            notices.append({"currency": item.currency, "movement_pct": str(movement.quantize(Decimal('0.01')))})
        updated += 1
    if not updated:
        raise http_error(422, {"rates": "None of the supplied currencies exist in this deployment."})
    if notices:
        recipients = db.scalars(select(User).where(User.tenant_id == actor.tenant_id, User.is_active.is_(True), User.level.in_(["Administrator", "Manager", "Executive"]))).all()
        summary = ", ".join(f"{x['currency']} {x['movement_pct']}%" for x in notices)
        for recipient in recipients:
            db.add(Notification(**stamp(actor), recipient_id=recipient.id, key=f"fx-movement:{payload.effective_date}:{recipient.id}", category="system_failures", severity="warning", message=f"Exchange-rate movement exceeded {settings.fx_movement_notice_pct}%: {summary}"))
    audit(db, actor, "Exchange rate table refreshed", detail=f"{payload.source} · {payload.effective_date}", after={"currencies": updated, "movement_notices": notices})
    return {"updated": updated, "movement_notices": notices}


@router.post("/commercial/rates/refresh/")
def refresh_rates(payload: RateRefreshInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level != "Administrator":
        raise http_error(403, "Workspace Administrator access is required.")
    result = apply_rate_refresh(db, user, payload)
    db.commit()
    return result


@router.post("/commercial/rates/rebaseline/")
def rebaseline_rates(payload: RebaselineInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level != "Administrator":
        raise http_error(403, "Workspace Administrator access is required.")
    opportunities = db.scalars(scoped(db, Opportunity, user).where(Opportunity.id.in_(payload.opportunity_ids)).options(selectinload(Opportunity.pursuit))).all()
    found = {item.id for item in opportunities}
    if found != set(payload.opportunity_ids):
        raise http_error(404, "One or more selected opportunities were not found in this deployment.")
    changed = []
    for opportunity in opportunities:
        if opportunity.stage not in OPEN_STAGES:
            raise http_error(422, {"opportunity_ids": f"{opportunity.pursuit.name} is closed and cannot be re-baselined."})
        rate = db.scalar(scoped(db, ExchangeRate, user).where(ExchangeRate.currency == opportunity.currency))
        if not rate:
            raise http_error(422, {"opportunity_ids": f"No reference rate exists for {opportunity.currency}."})
        old = opportunity.fx_rate
        if old == rate.rate:
            continue
        opportunity.fx_rate = rate.rate; opportunity.value_usd = money(opportunity.current_value * rate.rate); opportunity.updated_by_id = user.id
        db.add(ValueHistory(**stamp(user), opportunity_id=opportunity.id, value_type="Rate re-baseline", amount=opportunity.current_value, currency=opportunity.currency, fx_rate=rate.rate, note=payload.reason))
        audit(db, user, "Opportunity rate re-baselined", opportunity.pursuit, payload.reason, before={"rate": str(old)}, after={"rate": str(rate.rate)})
        changed.append(str(opportunity.id))
    db.commit()
    return {"changed": len(changed), "opportunity_ids": changed}


@router.get("/commercial/reports/undocumented-partners/")
def undocumented_partner_report(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level not in MANAGEMENT:
        raise http_error(403, "Management access is required for partner reports.")
    rows = db.scalars(scoped(db, PartnerInvolvement, user).where(PartnerInvolvement.status.in_(["Proposed", "Verbally agreed"])).options(selectinload(PartnerInvolvement.company), selectinload(PartnerInvolvement.contact), selectinload(PartnerInvolvement.opportunity).selectinload(Opportunity.pursuit))).all()
    return [{"partner_id": str(row.id), "opportunity_id": str(row.opportunity_id), "opportunity": row.opportunity.pursuit.name, "stage": row.opportunity.stage, "partner": row.company.name, "contact": row.contact.name, "status": row.status, "fee_basis": row.fee_basis} for row in rows if row.opportunity.stage in ADVANCED_STAGES]


@router.get("/commercial/reports/partner-performance/")
def partner_performance_report(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level not in MANAGEMENT:
        raise http_error(403, "Management access is required for partner reports.")
    rows = db.scalars(scoped(db, PartnerInvolvement, user).options(selectinload(PartnerInvolvement.company), selectinload(PartnerInvolvement.opportunity).selectinload(Opportunity.pursuit), selectinload(PartnerInvolvement.opportunity).selectinload(Opportunity.partners))).all()
    grouped: dict[UUID, dict] = {}
    for row in rows:
        group = grouped.setdefault(row.company_id, {"company_id": str(row.company_id), "partner": row.company.name, "opportunities_involved": set(), "opportunities_introduced": set(), "closed": set(), "won": set(), "net_value_usd": Decimal("0")})
        group["opportunities_involved"].add(row.opportunity_id)
        if row.introduced: group["opportunities_introduced"].add(row.opportunity_id)
        if row.opportunity.stage in {"won", "lost"}: group["closed"].add(row.opportunity_id)
        if row.opportunity.stage == "won":
            first_win_for_partner = row.opportunity_id not in group["won"]
            group["won"].add(row.opportunity_id)
            if first_win_for_partner:
                value = commercial_totals(db, row.opportunity)["net_usd"]
                if value is not None: group["net_value_usd"] += value
    result = []
    for group in grouped.values():
        closed = len(group["closed"]); won = len(group["won"])
        result.append({"company_id": group["company_id"], "partner": group["partner"], "opportunities_involved": len(group["opportunities_involved"]), "opportunities_introduced": len(group["opportunities_introduced"]), "wins": won, "closed": closed, "win_rate_pct": str((Decimal(won) / Decimal(closed) * 100).quantize(Decimal('0.01'))) if closed else None, "net_value_usd": str(money(group["net_value_usd"]))})
    return sorted(result, key=lambda row: (-row["opportunities_involved"], row["partner"]))
