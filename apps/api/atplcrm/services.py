from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from .constants import MANAGEMENT
from .models import AuditEvent, Opportunity, PartnerInvolvement, Pursuit, TeamRole, User, ValueHistory


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


def net_usd(db: Session, opportunity: Opportunity) -> Decimal | None:
    deduction = Decimal("0")
    partners = db.scalars(scoped(db, PartnerInvolvement, opportunity).where(PartnerInvolvement.opportunity_id == opportunity.id)).all()
    for partner in partners:
        if partner.fee_basis == "Percentage of contract value":
            deduction += opportunity.current_value * partner.share_pct / 100
        elif partner.fee_basis == "Fixed fee":
            deduction += partner.fixed_fee
        else:
            return None
    return money((opportunity.current_value - deduction) * opportunity.fx_rate)


def flags(pursuit: Pursuit) -> list[str]:
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
        working_days = sum(1 for offset in range((today - pursuit.ready_at.date()).days) if (pursuit.ready_at.date() + timedelta(days=offset + 1)).weekday() < 5)
        if working_days > 5:
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
