from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .constants import MANAGEMENT
from .models import AuditEvent, CommercialSetting, Opportunity, PartnerInvolvement, Pursuit, TeamRole, User, ValueHistory


def utc(value: datetime) -> datetime:
    """Normalize database datetimes; SQLite drops timezone metadata in tests."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def http_error(code: int, detail: str | dict) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def stamp(user: User) -> dict:
    return {"tenant_id": user.tenant_id, "created_by_id": user.id, "updated_by_id": user.id}


def scoped(db: Session, model, user: User):
    return select(model).where(model.tenant_id == user.tenant_id, model.is_deleted.is_(False))


def get_scoped(db: Session, model, user: User, identifier: UUID):
    item = db.scalar(scoped(db, model, user).where(model.id == identifier))
    if not item:
        raise http_error(status.HTTP_404_NOT_FOUND, "Record not found.")
    return item


def team_member(db: Session, user: User, pursuit: Pursuit) -> bool:
    if user.id in {pursuit.owner_id, pursuit.sourced_by_id, pursuit.holder_id}:
        return True
    return db.scalar(select(TeamRole.id).where(TeamRole.pursuit_id == pursuit.id, TeamRole.user_id == user.id, TeamRole.is_deleted.is_(False)).limit(1)) is not None


def can_work(db: Session, user: User, pursuit: Pursuit) -> bool:
    return user.tenant_id == pursuit.tenant_id and (user.level in MANAGEMENT or team_member(db, user, pursuit))


def require_work(db: Session, user: User, pursuit: Pursuit) -> None:
    if not can_work(db, user, pursuit):
        raise http_error(status.HTTP_403_FORBIDDEN, "Only the assigned team or management can change this pursuit.")


def can_value(db: Session, user: User, opportunity: Opportunity) -> bool:
    return user.tenant_id == opportunity.tenant_id and (not opportunity.restricted or user.level in MANAGEMENT or team_member(db, user, opportunity.pursuit))


def future_date(value: date, field: str = "action_date") -> date:
    if value <= date.today():
        raise http_error(status.HTTP_422_UNPROCESSABLE_ENTITY, {field: "Enter a date after today. Existing overdue actions remain editable."})
    return value


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def commercial_totals(db: Session, opportunity: Opportunity) -> dict:
    deduction = Decimal("0")
    total_share = Decimal("0")
    unresolved: list[str] = []
    partners = db.scalars(scoped(db, PartnerInvolvement, opportunity).where(PartnerInvolvement.opportunity_id == opportunity.id)).all()
    for partner in partners:
        if partner.status == "Lapsed or superseded":
            continue
        if partner.fee_basis == "Percentage of contract value":
            deduction += opportunity.current_value * partner.share_pct / 100
            total_share += partner.share_pct
        elif partner.fee_basis == "Commission":
            deduction += opportunity.current_value * partner.share_pct / 100
            total_share += partner.share_pct
        elif partner.fee_basis == "Percentage of gross margin":
            total_share += partner.share_pct
            if opportunity.gross_margin_pct is None:
                unresolved.append("Gross margin is required for percentage-of-margin partner terms.")
            else:
                deduction += opportunity.current_value * opportunity.gross_margin_pct / 100 * partner.share_pct / 100
        elif partner.fee_basis == "Fixed fee":
            deduction += partner.fixed_fee
        elif partner.fee_basis == "Rate card spread":
            if partner.share_pct > 0:
                deduction += opportunity.current_value * partner.share_pct / 100
                total_share += partner.share_pct
            elif partner.fixed_fee > 0:
                deduction += partner.fixed_fee
            else:
                unresolved.append("Rate-card spread terms are incomplete.")
        else:
            unresolved.append("Partner terms are still to be agreed.")
    settings = db.scalar(scoped(db, CommercialSetting, opportunity))
    ceiling = settings.partner_share_warning_pct if settings else Decimal("40")
    if total_share > ceiling:
        unresolved.append(f"Partner share {total_share}% exceeds the configured {ceiling}% warning ceiling.")
    net_local = money(opportunity.current_value - deduction)
    if net_local < 0:
        unresolved.append("Partner deductions exceed the opportunity value.")
    calculable = not any(message for message in unresolved if "exceeds the configured" not in message)
    return {
        "gross_local": money(opportunity.current_value),
        "deduction_local": money(deduction),
        "net_local": net_local if calculable else None,
        "net_usd": money(net_local * opportunity.fx_rate) if calculable else None,
        "total_partner_share_pct": total_share.quantize(Decimal("0.01")),
        "warning_ceiling_pct": ceiling,
        "warnings": unresolved,
        "calculable": calculable,
    }


def net_usd(db: Session, opportunity: Opportunity) -> Decimal | None:
    return commercial_totals(db, opportunity)["net_usd"]


def flags(db: Session, pursuit: Pursuit) -> list[str]:
    now = datetime.now(timezone.utc)
    today = date.today()
    if pursuit.opportunity and pursuit.opportunity.stage in {"won", "lost"}:
        return []
    if not pursuit.opportunity and pursuit.lead and pursuit.lead.status == "closed":
        return []
    result: list[str] = []
    if pursuit.action_date < today:
        result.append("Overdue action")
    if (now - utc(pursuit.ball_since)).days > 14:
        result.append("Held over 14 days")
    if pursuit.blocker != "None":
        result.append("Blocked over 10 days" if pursuit.blocked_since and (now - utc(pursuit.blocked_since)).days > 10 else "Blocked")
    if (now - utc(pursuit.last_client_interaction or pursuit.created_at)).days >= 21:
        result.append("No recent client contact")
    if pursuit.opportunity and pursuit.opportunity.stage not in {"won", "lost", "hold"} and pursuit.opportunity.expected_close_date < today:
        result.append("Close date passed")
    if pursuit.lead and pursuit.lead.status == "ready" and pursuit.ready_at:
        from .calendar import tenant_calendar, working_days
        if working_days(pursuit.ready_at, today, tenant_calendar(db, pursuit.tenant_id)) > 5:
            result.append("Validation overdue")
    return result


def audit(db: Session, user: User, action: str, pursuit: Pursuit | None = None, detail: str = "", before: dict | None = None, after: dict | None = None) -> AuditEvent:
    event = AuditEvent(**stamp(user), pursuit_id=pursuit.id if pursuit else None, action=action, detail=detail, before=before or {}, after=after or {})
    db.add(event)
    return event


def record_value(db: Session, user: User, opportunity: Opportunity, amount: Decimal, value_type: str, note: str = "") -> None:
    opportunity.current_value = amount
    opportunity.value_usd = money(amount * opportunity.fx_rate)
    opportunity.updated_by_id = user.id
    db.add(ValueHistory(**stamp(user), opportunity_id=opportunity.id, value_type=value_type, amount=amount, currency=opportunity.currency, fx_rate=opportunity.fx_rate, note=note))
