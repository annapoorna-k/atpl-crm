from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import median
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .api import load_pursuit, tenant_user
from .calendar import tenant_calendar, working_days
from .database import get_db
from .constants import MANAGEMENT, STAGES
from .models import AuditEvent, Opportunity, Pursuit, PursuitAction, User
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
    calendar = tenant_calendar(db, user.tenant_id)
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
                    values.append(working_days(previous, completed, calendar))
        elapsed = float(median(values)) if values else None
        target = MILESTONE_TARGETS[key]
        result.append({"key": key, "label": label, "count": count, "median_working_days": elapsed, "target_working_days": target, "healthy": elapsed is None or key == "lead_created" or elapsed < target})
    return result


@router.get("/movement/")
def movement_report(period: str="90d",db: Session=Depends(get_db),user: User=Depends(current_user)):
    if user.level not in MANAGEMENT: raise http_error(403,"Management access is required for movement analysis.")
    if period not in {"30d","90d","365d","all"}: raise http_error(422,{"period":"Choose 30d, 90d, 365d or all."})
    cutoff=None if period=="all" else datetime.now(timezone.utc)-timedelta(days=int(period[:-1])); cal=tenant_calendar(db,user.tenant_id); labels=dict(STAGES); rank={x:i for i,x in enumerate(["discovery","presales","proposal","negotiation","contract","won","lost"])}
    rows=db.execute(select(AuditEvent,Pursuit).join(Pursuit,Pursuit.id==AuditEvent.pursuit_id).where(AuditEvent.tenant_id==user.tenant_id,AuditEvent.action=="Stage changed",AuditEvent.is_deleted.is_(False)).options(selectinload(Pursuit.company)).order_by(AuditEvent.created_at)).all(); transitions=defaultdict(list); last={}; latest={}; moves=[]
    for event,pursuit in rows:
        a=str((event.before or {}).get("stage","")); b=str((event.after or {}).get("stage",""));
        if not a or not b: continue
        elapsed=working_days(last.get(pursuit.id) or pursuit.validated_at or pursuit.created_at,event.created_at,cal); last[pursuit.id]=event.created_at; latest[pursuit.id]=event.created_at
        if cutoff and utc(event.created_at)<cutoff: continue
        transitions[(a,b)].append(elapsed); backward=a in rank and b in rank and rank[b]<rank[a]; moves.append({"pursuit_id":str(pursuit.id),"pursuit":pursuit.name,"company":pursuit.company.name,"from_label":labels.get(a,a),"to_label":labels.get(b,b),"moved_at":event.created_at,"working_days_in_previous_stage":elapsed,"evidence":event.detail,"regression":backward})
    ages=defaultdict(list); now=datetime.now(timezone.utc)
    for item in db.scalars(scoped(db,Opportunity,user).where(Opportunity.stage.notin_(["won","lost"])).options(selectinload(Opportunity.pursuit))).all(): ages[item.stage].append(working_days(latest.get(item.pursuit_id) or item.pursuit.validated_at or item.pursuit.created_at,now,cal))
    return {"period":period,"move_count":len(moves),"regression_count":sum(x["regression"] for x in moves),"transitions":[{"from_label":labels.get(a,a),"to_label":labels.get(b,b),"count":len(v),"median_working_days":float(median(v))} for (a,b),v in transitions.items()],"current_stage_age":[{"stage":a,"label":labels.get(a,a),"count":len(v),"median_working_days":float(median(v)),"oldest_working_days":max(v)} for a,v in ages.items()],"moves":list(reversed(moves[-100:])),"calendar":{"working_weekdays":cal.working_weekdays if cal else [0,1,2,3,4],"holiday_count":len(cal.holidays) if cal else 0}}
