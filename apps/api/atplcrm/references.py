from sqlalchemy import select
from sqlalchemy.orm import Session
from .constants import REFERENCE_DEFAULTS
from .models import User, WorkspaceReference
from .services import http_error

def rows(db: Session, user: User, *, active_only: bool = True) -> list[WorkspaceReference]:
    statement = select(WorkspaceReference).where(WorkspaceReference.tenant_id == user.tenant_id, WorkspaceReference.is_deleted.is_(False))
    if active_only: statement = statement.where(WorkspaceReference.active.is_(True))
    return list(db.scalars(statement.order_by(WorkspaceReference.category, WorkspaceReference.sort_order, WorkspaceReference.label)).all())

def grouped(db: Session, user: User, *, active_only: bool = True) -> dict[str, list[WorkspaceReference]]:
    result: dict[str, list[WorkspaceReference]] = {}
    for item in rows(db, user, active_only=active_only): result.setdefault(item.category, []).append(item)
    return result

def codes(db: Session, user: User, category: str) -> set[str]:
    configured = grouped(db, user).get(category, [])
    return {item.code for item in configured} if configured else {code for code, _label, _number in REFERENCE_DEFAULTS[category]}

def require_code(db: Session, user: User, category: str, code: str, field: str) -> str:
    if code not in codes(db, user, category): raise http_error(422, {field: "Choose an active workspace option."})
    return code

def probability(db: Session, user: User, stage: str) -> int:
    item = db.scalar(select(WorkspaceReference).where(WorkspaceReference.tenant_id == user.tenant_id, WorkspaceReference.category == "stages", WorkspaceReference.code == stage, WorkspaceReference.active.is_(True), WorkspaceReference.is_deleted.is_(False)))
    if item and item.numeric_value is not None: return item.numeric_value
    for code, _label, number in REFERENCE_DEFAULTS["stages"]:
        if code == stage and number is not None: return number
    raise http_error(422, {"stage": "Choose an active workspace stage."})

def contract(db: Session, user: User) -> dict:
    configured = grouped(db, user)
    def pairs(category: str) -> list[list[str]]:
        values = configured.get(category)
        return [[item.code, item.label] for item in values] if values else [[code, label] for code, label, _number in REFERENCE_DEFAULTS[category]]
    stages = configured.get("stages")
    probabilities = {item.code: item.numeric_value or 0 for item in stages} if stages else {code: number or 0 for code, _label, number in REFERENCE_DEFAULTS["stages"]}
    return {"stages": pairs("stages"), "probabilities": probabilities, "lead_statuses": pairs("lead_statuses"), "sources": pairs("sources"), "services": pairs("services"), "actions": pairs("actions"), "blockers": pairs("blockers"), "loss_reasons": pairs("loss_reasons"), "disqualification_reasons": pairs("disqualification_reasons"), "request_statuses": pairs("request_statuses")}
