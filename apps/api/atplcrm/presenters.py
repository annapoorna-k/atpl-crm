from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Activity, Company, Contact, Opportunity, PreSalesRequest, Pursuit, PursuitAction, User
from .references import probability as stage_probability
from .services import can_value, can_work, flags, net_usd, utc


MILESTONES = (
    ("lead_created", "Lead created", "created_at"),
    ("first_contacted", "First contacted", "first_contacted_at"),
    ("ready_for_validation", "Ready for validation", "ready_at"),
    ("validated", "Validated", "validated_at"),
    ("presales_assigned", "Pre-sales assigned", "presales_assigned_at"),
    ("proposal_sent", "Proposal sent", "proposal_sent_at"),
    ("closed", "Closed", "closed_at"),
)


def milestones(item: Pursuit) -> list[dict]:
    return [{"key": key, "label": label, "at": getattr(item, attribute)} for key, label, attribute in MILESTONES]


def person(user: User) -> dict:
    return {"id": user.id, "name": user.display_name, "first_name": user.first_name, "last_name": user.last_name, "level": user.level, "job_title": user.job_title, "email": user.email, "active": user.is_active}


def company(item: Company) -> dict:
    return {"id": str(item.id), "name": item.name, "domain": item.domain, "company_type": item.company_type, "industry": item.industry, "country": item.country, "owner_id": item.owner_id, "owner": item.owner.display_name, "global_account_name": item.global_account_name, "primary_region": item.primary_region}


def contact(db: Session, item: Contact) -> dict:
    touch_count = db.scalar(select(func.count(Activity.id)).where(Activity.contact_id == item.id, Activity.is_deleted.is_(False), Activity.direction == "Outbound", Activity.activity_type != "Internal note")) or 0
    last_touch = db.scalar(select(func.max(Activity.activity_date)).where(Activity.contact_id == item.id, Activity.is_deleted.is_(False)))
    return {"id": str(item.id), "name": item.name, "first_name": item.first_name, "last_name": item.last_name, "company_id": str(item.company_id), "company": item.company.name, "email": item.email, "job_title": item.job_title, "phone": item.phone, "mobile": item.mobile, "country": item.country, "city": item.city, "seniority": item.seniority, "linkedin_url": item.linkedin_url, "owner_id": item.owner_id, "owner": item.owner.display_name, "source_channel": item.source_channel, "source_detail": item.source_detail, "engagement_status": item.engagement_status, "do_not_contact": item.do_not_contact, "consent_basis": item.consent_basis, "notes": item.notes, "touch_count": touch_count, "last_touched_at": last_touch}


def pursuit(db: Session, item: Pursuit, user: User) -> dict:
    opportunity = item.opportunity
    visible = not opportunity or can_value(db, user, opportunity)
    return {"id": str(item.id), "name": item.name, "company_id": str(item.company_id), "company": item.company.name, "owner": item.owner.display_name, "owner_id": item.owner_id, "sourced_by": item.sourced_by.display_name, "holder": item.holder.display_name, "holder_id": item.holder_id, "ball_since": item.ball_since, "days_held": (datetime.now(timezone.utc) - utc(item.ball_since)).days, "next_action": item.next_action, "action_type": item.action_type, "action_date": item.action_date, "priority": item.priority, "source_channel": item.source_channel, "source_detail": item.source_detail, "blocker": item.blocker, "blocker_owner": item.blocker_owner.display_name if item.blocker_owner else None, "blocker_owner_id": item.blocker_owner_id, "resolution_action": item.resolution_action, "days_blocked": (datetime.now(timezone.utc) - utc(item.blocked_since)).days if item.blocked_since else 0, "last_client_interaction": item.last_client_interaction, "next_meeting": item.next_meeting, "created_at": item.created_at, "version": item.version, "flags": flags(item), "can_work": can_work(db, user, item), "lead_id": str(item.lead.id), "opportunity_id": str(opportunity.id) if opportunity else None, "team": [{"user_id": role.user_id, "name": role.user.display_name, "role": role.role} for role in item.team if not role.is_deleted], "contacts": [{"link_id": str(role.id), "id": str(role.contact_id), "name": role.contact.name, "role": role.role, "job_title": role.contact.job_title, "email": role.contact.email} for role in item.stakeholders if not role.is_deleted], "milestones": milestones(item), "values_visible": visible}


def lead(db: Session, item, user: User) -> dict:
    return {**pursuit(db, item.pursuit, user), "lead_id": str(item.id), "status": item.status, "area_of_interest": item.area_of_interest, "outcome": item.outcome, "reason": item.reason, "revisit_date": item.revisit_date}


def opportunity(db: Session, item: Opportunity, user: User) -> dict:
    data = {**pursuit(db, item.pursuit, user), "stage": item.stage, "opportunity_type": item.opportunity_type, "customer_need": item.customer_need, "scope_summary": item.scope_summary, "service_line": item.service_line, "engagement_type": item.engagement_type, "primary_contact_id": str(item.primary_contact_id), "primary_contact": item.primary_contact.name, "expected_close_date": item.expected_close_date, "probability": item.probability, "probability_note": item.probability_note, "stage_probability": stage_probability(db, user, item.stage), "restricted": item.restricted, "revisit_date": item.revisit_date, "loss_reason": item.loss_reason, "contract_number": item.contract_number, "approval_recorded": item.approval_recorded}
    if can_value(db, user, item):
        net = net_usd(db, item)
        data.update(current_value=str(item.current_value), currency=item.currency, fx_rate=str(item.fx_rate), value_usd=str(item.value_usd), net_value_usd=str(net) if net is not None else None, values=[{"id": str(value.id), "type": value.value_type, "amount": str(value.amount), "currency": value.currency, "date": value.created_at, "note": value.note} for value in sorted(item.values, key=lambda row: row.created_at, reverse=True)])
    return data


def activity(item: Activity) -> dict:
    return {"id": str(item.id), "subject": item.subject, "notes": item.notes, "activity_type": item.activity_type, "is_client_facing": item.is_client_facing, "date": item.activity_date, "direction": item.direction, "outcome": item.outcome, "author": item.created_by.display_name if item.created_by else "System", "company": item.company.name, "contact_id": str(item.contact_id) if item.contact_id else None, "pursuit_id": str(item.pursuit_id) if item.pursuit_id else None}


def completed_action(item: PursuitAction) -> dict:
    return {"id": str(item.id), "summary": item.summary, "action_type": item.action_type, "due_date": item.due_date, "outcome": item.outcome, "note": item.note, "completed_at": item.completed_at, "completed_by": item.completed_by.display_name}


def request(item: PreSalesRequest) -> dict:
    return {"id": str(item.id), "title": item.title, "request_type": item.request_type, "status": item.status, "assigned_to": item.assigned_to.display_name, "assigned_to_id": item.assigned_to_id, "needed_by": item.needed_by, "estimated_days": str(item.estimated_days), "actual_days": str(item.actual_days) if item.actual_days is not None else None, "opportunity": item.opportunity.pursuit.name, "opportunity_id": str(item.opportunity_id), "pursuit_id": str(item.opportunity.pursuit_id), "notes": item.notes, "blocked_reason": item.blocked_reason}
