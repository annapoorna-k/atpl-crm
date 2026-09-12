from datetime import date, datetime, timezone
from statistics import median
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .api import load_pursuit, tenant_user
from .database import get_db
from .models import Pursuit, PursuitAction, User
from .presenters import MILESTONES, completed_action
from .references import require_code
from .schemas import ActionCompletionInput
from .security import current_user
from .services import audit, future_date, http_error, require_work, scoped, stamp, utc

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

MILESTONE_TARGETS = {
    "lead_created": 0,
    "first_contacted": 3,
    "ready_for_validation": 15,
    "validated": 5,
    "presales_assigned": 3,
    "proposal_sent": 20,
    "closed": 45,
}


def working_days(start: datetime, end: datetime) -> int:
    start_date, end_date = utc(start).date(), utc(end).date()
    if end_date <= start_date:
        return 0
    return sum(1 for offset in range((end_date - start_date).days) if (start_date.fromordinal(start_date.toordinal() + offset)).weekday() < 5)


@router.post("/pursuits/{identifier}/actions/complete/")
def complete_pursuit_action(identifier: UUID, payload: ActionCompletionInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, identifier, lock=True)
    require_work(db, user, pursuit)
    if (pursuit.opportunity and pursuit.opportunity.stage in {"won", "lost"}) or (not pursuit.opportunity and pursuit.lead.status == "closed"):
        raise http_error(422, "Closed pursuits cannot accept another action.")
    if payload.version != pursuit.version:
        raise http_error(409, "This pursuit changed. Refresh before completing the action.")
    holder = tenant_user(db, user, payload.next_holder)
    require_code(db, user, "actions", payload.next_action_type, "next_action_type")
    next_date = future_date(payload.next_action_date, "next_action_date")
    prior = {"holder": pursuit.holder_id, "action": pursuit.next_action, "action_type": pursuit.action_type, "date": str(pursuit.action_date), "version": pursuit.version}
    action = PursuitAction(
        **stamp(user), pursuit_id=pursuit.id, summary=pursuit.next_action,
        action_type=pursuit.action_type, due_date=pursuit.action_date,
        outcome=payload.outcome, note=payload.note,
        completed_at=datetime.now(timezone.utc), completed_by_id=user.id,
    )
    db.add(action)
    if pursuit.holder_id != holder.id:
        pursuit.ball_since = datetime.now(timezone.utc)
    pursuit.holder_id = holder.id
    pursuit.next_action = payload.next_action
    pursuit.action_type = payload.next_action_type
    pursuit.action_date = next_date
    pursuit.version += 1
    pursuit.updated_by_id = user.id
    audit(db, user, "Action completed", pursuit, payload.outcome, before=prior, after={"holder": holder.id, "action": pursuit.next_action, "action_type": pursuit.action_type, "date": str(pursuit.action_date), "version": pursuit.version})
    db.commit()
    return completed_action(db.scalar(scoped(db, PursuitAction, user).where(PursuitAction.id == action.id).options(selectinload(PursuitAction.completed_by))))


@router.get("/pursuits/{identifier}/actions/")
def pursuit_actions(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, identifier)
    rows = db.scalars(scoped(db, PursuitAction, user).where(PursuitAction.pursuit_id == pursuit.id).options(selectinload(PursuitAction.completed_by)).order_by(PursuitAction.completed_at.desc())).all()
    return [completed_action(row) for row in rows]


@router.get("/milestones/")
def milestone_report(db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuits = db.scalars(scoped(db, Pursuit, user)).all()
    result = []
    for index, (key, label, attribute) in enumerate(MILESTONES):
        values = []
        count = 0
        for pursuit in pursuits:
            completed = getattr(pursuit, attribute)
            if not completed:
                continue
            count += 1
            if index == 0:
                values.append(0)
            else:
                previous = getattr(pursuit, MILESTONES[index - 1][2])
                if previous:
                    values.append(working_days(previous, completed))
        elapsed = float(median(values)) if values else None
        target = MILESTONE_TARGETS[key]
        result.append({"key": key, "label": label, "count": count, "median_working_days": elapsed, "target_working_days": target, "healthy": elapsed is None or key == "lead_created" or elapsed < target})
    return result
