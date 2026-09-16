from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from . import presenters as out
from .api import request_options, user_options
from .database import get_db
from .models import AutomationRun, Notification, NotificationPreference, Opportunity, PreSalesRequest, Pursuit, User
from .calendar import tenant_calendar, working_days
from .schemas import NotificationPreferenceInput
from .security import current_user
from .services import http_error, scoped, stamp, utc

router = APIRouter(prefix="/api/v1", tags=["work and notifications"])

PREFERENCE_FIELDS = (
    "due_actions", "stalled_pursuits", "blockers", "inactivity", "proposal_followup",
    "validation", "presales", "close_dates", "revisits", "system_failures", "weekly_summary",
)
TERMINAL_REQUEST_STATUSES = {"Delivered", "Cancelled"}


def active_pursuit(pursuit: Pursuit) -> bool:
    if pursuit.opportunity:
        return pursuit.opportunity.stage not in {"won", "lost"}
    return bool(pursuit.lead and pursuit.lead.status != "closed")


def preference(db: Session, user: User) -> NotificationPreference:
    item = db.scalar(scoped(db, NotificationPreference, user).where(NotificationPreference.user_id == user.id))
    if item:
        return item
    item = NotificationPreference(**stamp(user), user_id=user.id)
    db.add(item)
    db.flush()
    return item


def preference_data(item: NotificationPreference) -> dict:
    return {field: getattr(item, field) for field in PREFERENCE_FIELDS} | {
        "inactivity_days": item.inactivity_days,
        "proposal_followup_days": item.proposal_followup_days,
        "close_notice_days": item.close_notice_days,
    }


def notification_data(item: Notification) -> dict:
    return {
        "id": str(item.id), "message": item.message, "category": item.category,
        "severity": item.severity, "read": item.read, "read_at": item.read_at,
        "pursuit_id": str(item.pursuit_id) if item.pursuit_id else None,
        "created_at": item.created_at,
    }


def stable_key(category: str, identity: str, anchor: object) -> str:
    digest = hashlib.sha256(f"{category}:{identity}:{anchor}".encode()).hexdigest()[:32]
    return f"{category}:{digest}"


def emit(db: Session, system_user: User, recipient: User, category: str, message: str, key: str, *, pursuit: Pursuit | None = None, severity: str = "medium") -> int:
    prefs = preference(db, recipient)
    if category in PREFERENCE_FIELDS and not getattr(prefs, category):
        return 0
    if db.scalar(select(Notification.id).where(Notification.tenant_id == recipient.tenant_id, Notification.recipient_id == recipient.id, Notification.key == key)):
        return 0
    db.add(Notification(**stamp(system_user), recipient_id=recipient.id, pursuit_id=pursuit.id if pursuit else None, message=message, key=key, category=category, severity=severity))
    return 1


def tenant_context(db: Session, tenant_id: UUID):
    users = db.scalars(select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True))).all()
    if not users:
        return [], None, [], []
    system_user = next((user for user in users if user.level == "Administrator"), users[0])
    pursuits = db.scalars(select(Pursuit).where(Pursuit.tenant_id == tenant_id, Pursuit.is_deleted.is_(False)).options(*user_options())).unique().all()
    requests = db.scalars(select(PreSalesRequest).where(PreSalesRequest.tenant_id == tenant_id, PreSalesRequest.is_deleted.is_(False)).options(*request_options())).unique().all()
    return users, system_user, pursuits, requests


def title_heads(users: list[User], phrase: str) -> list[User]:
    phrase = phrase.lower().replace("-", "")
    return [user for user in users if phrase in user.job_title.lower().replace("-", "")]


def refresh_for_tenant(db: Session, tenant_id: UUID) -> int:
    users, system_user, pursuits, requests = tenant_context(db, tenant_id)
    if not system_user:
        return 0
    by_id = {user.id: user for user in users}
    sales_heads = title_heads(users, "head of sales")
    presales_heads = title_heads(users, "head of presales")
    today = date.today()
    now = datetime.now(timezone.utc)
    calendar = tenant_calendar(db, tenant_id)
    created = 0

    for pursuit in pursuits:
        if not active_pursuit(pursuit):
            continue
        holder, owner = by_id.get(pursuit.holder_id), by_id.get(pursuit.owner_id)
        if not holder or not owner:
            continue
        if pursuit.action_date <= today:
            overdue = pursuit.action_date < today
            created += emit(db, system_user, holder, "due_actions", f"{'Overdue' if overdue else 'Due today'}: {pursuit.next_action} · {pursuit.name}", stable_key("due_actions", str(pursuit.id), f"{pursuit.next_action}:{pursuit.action_date}"), pursuit=pursuit, severity="high" if overdue else "medium")
        if not pursuit.next_action.strip() or not pursuit.action_type.strip():
            for recipient in {holder, owner}:
                created += emit(db, system_user, recipient, "due_actions", f"Missing next action: {pursuit.name}", stable_key("due_actions", str(pursuit.id), "missing"), pursuit=pursuit, severity="high")
        held_days = (now - utc(pursuit.ball_since)).days
        if held_days > 14:
            relevant_heads = sales_heads if any(word in holder.job_title.lower() for word in ("sales", "account")) else presales_heads
            for recipient in {holder, *relevant_heads}:
                created += emit(db, system_user, recipient, "stalled_pursuits", f"Ball in Court held {held_days} days: {pursuit.name}", stable_key("stalled_pursuits", str(pursuit.id), pursuit.ball_since.date()), pursuit=pursuit, severity="high")
        if pursuit.blocker != "None" and pursuit.blocked_since and (now - utc(pursuit.blocked_since)).days > 10:
            recipients = {owner}
            if pursuit.blocker_owner_id in by_id:
                recipients.add(by_id[pursuit.blocker_owner_id])
            for recipient in recipients:
                created += emit(db, system_user, recipient, "blockers", f"Blocker unresolved for {(now - utc(pursuit.blocked_since)).days} days: {pursuit.blocker} · {pursuit.name}", stable_key("blockers", str(pursuit.id), pursuit.blocked_since.date()), pursuit=pursuit, severity="high")
        inactivity_anchor = pursuit.last_client_interaction or pursuit.created_at
        owner_prefs = preference(db, owner)
        inactive_days = (now - utc(inactivity_anchor)).days
        if inactive_days >= owner_prefs.inactivity_days:
            created += emit(db, system_user, owner, "inactivity", f"No client interaction for {inactive_days} days: {pursuit.name}", stable_key("inactivity", str(pursuit.id), inactivity_anchor.date()), pursuit=pursuit)
        if pursuit.opportunity and pursuit.proposal_sent_at:
            proposal_days = (now - utc(pursuit.proposal_sent_at)).days
            no_followup = not pursuit.last_client_interaction or utc(pursuit.last_client_interaction) <= utc(pursuit.proposal_sent_at)
            recipients = {owner, *sales_heads}
            for recipient in recipients:
                if no_followup and proposal_days >= preference(db, recipient).proposal_followup_days:
                    created += emit(db, system_user, recipient, "proposal_followup", f"Proposal has no recorded follow-up: {pursuit.name}", stable_key("proposal_followup", str(pursuit.id), pursuit.proposal_sent_at.date()), pursuit=pursuit, severity="high")
        if pursuit.lead and pursuit.lead.status == "ready" and pursuit.ready_at and working_days(pursuit.ready_at, now, calendar) > 5:
            for recipient in sales_heads:
                created += emit(db, system_user, recipient, "validation", f"Lead awaiting validation over 5 working days: {pursuit.name}", stable_key("validation", str(pursuit.id), pursuit.ready_at.date()), pursuit=pursuit, severity="high")
        if pursuit.opportunity and pursuit.opportunity.expected_close_date <= today + timedelta(days=owner_prefs.close_notice_days):
            passed = pursuit.opportunity.expected_close_date < today
            created += emit(db, system_user, owner, "close_dates", f"Expected close date {'passed' if passed else 'approaching'}: {pursuit.name}", stable_key("close_dates", str(pursuit.id), pursuit.opportunity.expected_close_date), pursuit=pursuit, severity="high" if passed else "medium")
        revisit = pursuit.opportunity.revisit_date if pursuit.opportunity and pursuit.opportunity.stage == "hold" else pursuit.lead.revisit_date if pursuit.lead and pursuit.lead.outcome == "Nurture" else None
        if revisit and revisit <= today:
            created += emit(db, system_user, owner, "revisits", f"Revisit date reached: {pursuit.name}", stable_key("revisits", str(pursuit.id), revisit), pursuit=pursuit, severity="high")

    for request in requests:
        if request.status in TERMINAL_REQUEST_STATUSES or request.needed_by > today + timedelta(days=2):
            continue
        pursuit = request.opportunity.pursuit
        assignee = by_id.get(request.assigned_to_id)
        recipients = {*presales_heads}
        if assignee:
            recipients.add(assignee)
        overdue = request.needed_by < today
        for recipient in recipients:
            created += emit(db, system_user, recipient, "presales", f"Pre-sales deliverable {'overdue' if overdue else 'due soon'}: {request.title} · {pursuit.name}", stable_key("presales", str(request.id), request.needed_by), pursuit=pursuit, severity="high" if overdue else "medium")
    return created


def weekly_summary_for_tenant(db: Session, tenant_id: UUID) -> int:
    users, system_user, pursuits, _requests = tenant_context(db, tenant_id)
    if not system_user:
        return 0
    leadership = [user for user in users if user.level in {"Manager", "Executive"}]
    open_pursuits = [pursuit for pursuit in pursuits if active_pursuit(pursuit)]
    blocked = sum(pursuit.blocker != "None" for pursuit in open_pursuits)
    overdue = sum(pursuit.action_date < date.today() for pursuit in open_pursuits)
    week = date.today().isocalendar()
    message = f"Weekly pipeline: {len(open_pursuits)} active pursuits · {overdue} overdue actions · {blocked} blockers"
    return sum(emit(db, system_user, recipient, "weekly_summary", message, stable_key("weekly_summary", str(recipient.id), f"{week.year}-{week.week}"), severity="info") for recipient in leadership)


def record_run(db: Session, tenant_id: UUID, system_user: User, task_name: str, started_at: datetime, status: str, created_count: int = 0, detail: str = "") -> AutomationRun:
    run = AutomationRun(**stamp(system_user), task_name=task_name, status=status, started_at=started_at, finished_at=datetime.now(timezone.utc), created_count=created_count, detail=detail[:1000])
    db.add(run)
    return run


@router.get("/work/")
def work_queues(db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuits = db.scalars(scoped(db, Pursuit, user).options(*user_options())).unique().all()
    active = [pursuit for pursuit in pursuits if active_pursuit(pursuit)]
    requests = db.scalars(scoped(db, PreSalesRequest, user).options(*request_options())).unique().all()
    today = date.today(); now = datetime.now(timezone.utc); calendar = tenant_calendar(db, user.tenant_id)
    mine = [pursuit for pursuit in active if pursuit.holder_id == user.id]
    my_work = {
        "overdue_actions": [out.pursuit(db, row, user) for row in mine if row.action_date < today],
        "today_actions": [out.pursuit(db, row, user) for row in mine if row.action_date == today],
        "upcoming_actions": [out.pursuit(db, row, user) for row in mine if row.action_date > today],
        "blockers": [out.pursuit(db, row, user) for row in active if row.blocker_owner_id == user.id and row.blocker != "None"],
        "deliverables": [out.request(row) for row in requests if row.assigned_to_id == user.id and row.status not in TERMINAL_REQUEST_STATUSES],
    }
    issues = []
    for pursuit in active:
        presented = out.pursuit(db, pursuit, user)
        candidates = []
        if pursuit.action_date < today: candidates.append(("overdue_action", "Overdue next action", "high"))
        if not pursuit.next_action.strip() or not pursuit.action_type.strip(): candidates.append(("missing_action", "Missing next action", "high"))
        if (now - utc(pursuit.ball_since)).days > 14: candidates.append(("stalled", f"Ball in Court held {(now - utc(pursuit.ball_since)).days} days", "high"))
        if pursuit.blocker != "None" and pursuit.blocked_since and (now - utc(pursuit.blocked_since)).days > 10: candidates.append(("blocker", f"Blocker unresolved {(now - utc(pursuit.blocked_since)).days} days", "high"))
        if (now - utc(pursuit.last_client_interaction or pursuit.created_at)).days >= 21: candidates.append(("inactive", "No client interaction for 21 days", "medium"))
        if pursuit.opportunity and pursuit.opportunity.expected_close_date < today: candidates.append(("expired_close", "Expected close date passed", "high"))
        if pursuit.lead and pursuit.lead.status == "ready" and pursuit.ready_at and working_days(pursuit.ready_at, now, calendar) > 5: candidates.append(("validation", "Validation overdue", "high"))
        issues.extend({"key": f"{kind}:{pursuit.id}", "kind": kind, "label": label, "severity": severity, "pursuit": presented, "request": None} for kind, label, severity in candidates)
    for request in requests:
        if request.status not in TERMINAL_REQUEST_STATUSES and request.needed_by < today:
            issues.append({"key": f"deliverable:{request.id}", "kind": "deliverable", "label": "Pre-sales deliverable overdue", "severity": "high", "pursuit": None, "request": out.request(request)})
    return {"my_work": my_work, "needs_attention": sorted(issues, key=lambda row: (row["severity"] != "high", row["label"]))}


@router.get("/notifications/preferences/")
def get_preferences(db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = preference(db, user); db.commit()
    return preference_data(item)


@router.patch("/notifications/preferences/")
def update_preferences(payload: NotificationPreferenceInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = preference(db, user)
    for field, value in payload.model_dump().items(): setattr(item, field, value)
    item.updated_by_id = user.id; db.commit()
    return preference_data(item)


@router.get("/notifications/history/")
def notification_history(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = scoped(db, Notification, user).where(Notification.recipient_id == user.id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [notification_data(row) for row in rows], "page": page, "page_size": page_size, "total": total}


@router.post("/notifications/{identifier}/read/")
def mark_one_read(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(scoped(db, Notification, user).where(Notification.id == identifier, Notification.recipient_id == user.id))
    if not item: raise http_error(404, "Notification not found.")
    item.read = True; item.read_at = datetime.now(timezone.utc); db.commit()
    return notification_data(item)


@router.post("/notifications/read/")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(current_user)):
    now = datetime.now(timezone.utc)
    for item in db.scalars(scoped(db, Notification, user).where(Notification.recipient_id == user.id, Notification.read.is_(False))).all():
        item.read = True; item.read_at = now
    db.commit(); return {"detail": "Notifications marked as read."}


@router.get("/notifications/status/")
def automation_status(db: Session = Depends(get_db), user: User = Depends(current_user)):
    latest = db.scalar(scoped(db, AutomationRun, user).order_by(AutomationRun.finished_at.desc()).limit(1))
    return {"latest": {"task_name": latest.task_name, "status": latest.status, "created_count": latest.created_count, "finished_at": latest.finished_at, "detail": latest.detail} if latest else None}


@router.post("/notifications/refresh/")
def manual_refresh(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level != "Administrator": raise http_error(403, "Only an Administrator can run notification automation manually.")
    started = datetime.now(timezone.utc)
    created = refresh_for_tenant(db, user.tenant_id)
    record_run(db, user.tenant_id, user, "attention-notifications", started, "Succeeded", created)
    db.commit()
    return {"created": created}
