"""Paginated lists, personal views, bulk assignment and stakeholder editing."""
from __future__ import annotations

import csv
import io
import json
from copy import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from . import presenters as out
from .api import user_options
from .constants import MANAGEMENT
from .database import get_db
from .models import Company, Contact, Lead, Opportunity, PartnerInvolvement, Pursuit, PursuitContact, SavedView, TeamRole, User
from .schemas import BulkAssignmentInput, SavedViewInput, SavedViewPatch, StakeholderInput, StakeholderPatch
from .security import current_user
from .services import audit, get_scoped, http_error, require_work, scoped, stamp

router = APIRouter(prefix="/api/v1/productivity", tags=["productivity"])
ENTITY_TYPES = {"companies", "contacts", "leads", "opportunities"}
ALLOWED_VIEW_FILTERS = {"q","owner_id","holder_id","status","country","source","service","priority","blocker","partner","action_from","action_to","interaction_from","interaction_to","close_period","close_from","close_to","value_min","value_max","sort","direction"}


def manager(user: User) -> None:
    if user.level not in MANAGEMENT:
        raise http_error(403, "Manager, Executive or Administrator access is required for bulk assignment.")


def tenant_user(db: Session, user: User, identifier: int | None) -> User | None:
    if identifier is None:
        return None
    item = db.scalar(select(User).where(User.id == identifier, User.tenant_id == user.tenant_id, User.is_active.is_(True)))
    if not item:
        raise http_error(422, {"user": "Select an active user from this workspace."})
    return item


def view_data(item: SavedView) -> dict:
    return {"id": str(item.id), "entity_type": item.entity_type, "name": item.name, "filters": item.filters, "created_at": item.created_at, "updated_at": item.updated_at}


def valid_filters(filters: dict) -> dict:
    unknown = set(filters) - ALLOWED_VIEW_FILTERS
    if unknown:
        raise http_error(422, {"filters": f"Unsupported filters: {', '.join(sorted(unknown))}."})
    return {key: value for key, value in filters.items() if value not in {None, "", "all"}}


@router.get("/views/")
def saved_views(entity_type: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    statement = scoped(db, SavedView, user).where(SavedView.owner_id == user.id)
    if entity_type:
        if entity_type not in ENTITY_TYPES: raise http_error(422, {"entity_type": "Unsupported record type."})
        statement = statement.where(SavedView.entity_type == entity_type)
    items = db.scalars(statement.order_by(SavedView.name)).all()
    return [view_data(item) for item in items]


@router.post("/views/", status_code=201)
def create_view(payload: SavedViewInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    duplicate = db.scalar(scoped(db, SavedView, user).where(SavedView.owner_id == user.id, SavedView.entity_type == payload.entity_type, func.lower(SavedView.name) == payload.name.casefold()))
    if duplicate: raise http_error(422, {"name": "You already have a view with this name for these records."})
    item = SavedView(**stamp(user), owner_id=user.id, entity_type=payload.entity_type, name=payload.name, filters=valid_filters(payload.filters))
    db.add(item); audit(db, user, "Saved view created", detail=f"{payload.entity_type}: {payload.name}"); db.commit(); db.refresh(item)
    return view_data(item)


@router.patch("/views/{identifier}/")
def update_view(identifier: UUID, payload: SavedViewPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(scoped(db, SavedView, user).where(SavedView.id == identifier, SavedView.owner_id == user.id))
    if not item: raise http_error(404, "Saved view not found.")
    values = payload.model_dump(exclude_unset=True)
    if "filters" in values: values["filters"] = valid_filters(values["filters"] or {})
    if "name" in values:
        duplicate = db.scalar(scoped(db, SavedView, user).where(SavedView.owner_id == user.id, SavedView.entity_type == item.entity_type, func.lower(SavedView.name) == values["name"].casefold(), SavedView.id != item.id))
        if duplicate: raise http_error(422, {"name": "You already have a view with this name for these records."})
    for key, value in values.items(): setattr(item, key, value)
    item.updated_by_id = user.id; audit(db, user, "Saved view updated", detail=item.name); db.commit(); db.refresh(item)
    return view_data(item)


@router.delete("/views/{identifier}/")
def delete_view(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(scoped(db, SavedView, user).where(SavedView.id == identifier, SavedView.owner_id == user.id))
    if not item: raise http_error(404, "Saved view not found.")
    item.is_deleted = True; item.updated_by_id = user.id; audit(db, user, "Saved view deleted", detail=item.name); db.commit()
    return {"detail": "Saved view deleted."}


def paginated(db: Session, statement, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return total, items


def exported_list(entity_type: str, payload: list[dict], export_format: str):
    headers = list(payload[0]) if payload else ["No matching records"]
    rows = []
    for item in payload:
        row = {}
        for key, value in item.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, default=str, ensure_ascii=False)
            elif value is not None and not isinstance(value, (str, int, float, bool)):
                value = value.isoformat() if isinstance(value, (date, datetime)) else str(value)
            row[key] = value
        rows.append(row)
    if export_format == "csv":
        stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=headers); writer.writeheader()
        for row in rows:
            writer.writerow({key: f"'{value}" if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for key, value in row.items()})
        payload_bytes = stream.getvalue().encode("utf-8-sig"); media = "text/csv; charset=utf-8"
    else:
        book = Workbook(); sheet = book.active; sheet.title = entity_type[:31]; sheet.append(headers)
        for row in rows: sheet.append([row.get(header) for header in headers])
        for cell in sheet[1]:
            font = copy(cell.font); font.bold = True; cell.font = font
        output = io.BytesIO(); book.save(output); payload_bytes = output.getvalue(); media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(io.BytesIO(payload_bytes), media_type=media, headers={"Content-Disposition": f'attachment; filename="ATPLCRM-{entity_type}-{date.today()}.{export_format}"'})


@router.get("/lists/{entity_type}/")
def record_list(
    entity_type: str,
    q: str = Query("", max_length=120),
    owner_id: int | None = None,
    holder_id: int | None = None,
    action_from: date | None = None, action_to: date | None = None,
    interaction_from: date | None = None, interaction_to: date | None = None,
    blocker: str = "", partner: str = "", close_period: str = "", close_from: date | None = None, close_to: date | None = None,
    value_min: Decimal | None = Query(None, ge=0), value_max: Decimal | None = Query(None, ge=0),
    status: str = "",
    country: str = "",
    source: str = "",
    service: str = "",
    priority: str = "",
    sort: str = "updated",
    direction: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=10, le=100),
    export_format: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if entity_type not in ENTITY_TYPES: raise http_error(404, "Record list not found.")
    if export_format not in {"", "csv", "xlsx"}: raise http_error(422, {"export_format": "Choose csv or xlsx."})
    if export_format: page, page_size = 1, 50000
    if action_from and action_to and action_from > action_to: raise http_error(422, {"action_to": "End date must be on or after the start date."})
    if interaction_from and interaction_to and interaction_from > interaction_to: raise http_error(422, {"interaction_to": "End date must be on or after the start date."})
    if close_from and close_to and close_from > close_to: raise http_error(422, {"close_to": "End date must be on or after the start date."})
    if value_min is not None and value_max is not None and value_min > value_max: raise http_error(422, {"value_max": "Maximum value must be at least the minimum value."})
    descending = direction != "asc"; needle = f"%{q.strip()}%"
    if entity_type == "companies":
        statement = scoped(db, Company, user).options(selectinload(Company.owner))
        if q: statement = statement.where(or_(Company.name.ilike(needle), Company.domain.ilike(needle), Company.industry.ilike(needle)))
        if owner_id: statement = statement.where(Company.owner_id == owner_id)
        if country: statement = statement.where(func.lower(Company.country) == country.casefold())
        columns = {"name": Company.name, "country": Company.country, "created": Company.created_at, "updated": Company.updated_at}
        order = columns.get(sort, Company.updated_at); statement = statement.order_by(order.desc() if descending else order.asc(), Company.id)
        total, items = paginated(db, statement, page, page_size); payload = [out.company(item) for item in items]
    elif entity_type == "contacts":
        statement = scoped(db, Contact, user).options(selectinload(Contact.company), selectinload(Contact.owner))
        if q: statement = statement.where(or_(Contact.first_name.ilike(needle), Contact.last_name.ilike(needle), Contact.email.ilike(needle), Contact.phone.ilike(needle), Contact.mobile.ilike(needle)))
        if owner_id: statement = statement.where(Contact.owner_id == owner_id)
        if country: statement = statement.where(func.lower(Contact.country) == country.casefold())
        if status: statement = statement.where(Contact.engagement_status == status)
        columns = {"name": Contact.last_name, "country": Contact.country, "created": Contact.created_at, "updated": Contact.updated_at}
        order = columns.get(sort, Contact.updated_at); statement = statement.order_by(order.desc() if descending else order.asc(), Contact.id)
        total, items = paginated(db, statement, page, page_size); payload = [out.contact(db, item) for item in items]
    elif entity_type == "leads":
        statement = scoped(db, Lead, user).join(Lead.pursuit).join(Pursuit.company).options(selectinload(Lead.pursuit).options(*user_options()))
        if q: statement = statement.where(or_(Pursuit.name.ilike(needle), Company.name.ilike(needle), Pursuit.source_detail.ilike(needle)))
        if owner_id: statement = statement.where(Pursuit.owner_id == owner_id)
        if status: statement = statement.where(Lead.status == status)
        if country: statement = statement.where(func.lower(Company.country) == country.casefold())
        if source: statement = statement.where(Pursuit.source_channel == source)
        if priority: statement = statement.where(Pursuit.priority == priority)
        if holder_id: statement=statement.where(Pursuit.holder_id==holder_id)
        if action_from: statement=statement.where(Pursuit.action_date>=action_from)
        if action_to: statement=statement.where(Pursuit.action_date<=action_to)
        if interaction_from: statement=statement.where(Pursuit.last_client_interaction>=datetime.combine(interaction_from,datetime.min.time(),tzinfo=timezone.utc))
        if interaction_to: statement=statement.where(Pursuit.last_client_interaction<datetime.combine(interaction_to+timedelta(days=1),datetime.min.time(),tzinfo=timezone.utc))
        columns = {"name": Pursuit.name, "action_date": Pursuit.action_date, "last_interaction": Pursuit.last_client_interaction, "created": Pursuit.created_at, "updated": Pursuit.updated_at}
        order = columns.get(sort, Pursuit.updated_at); statement = statement.order_by(order.desc() if descending else order.asc(), Lead.id)
        total, items = paginated(db, statement, page, page_size); payload = [out.lead(db, item, user) for item in items]
    else:
        statement = scoped(db, Opportunity, user).join(Opportunity.pursuit).join(Pursuit.company).options(selectinload(Opportunity.pursuit).options(*user_options()), selectinload(Opportunity.primary_contact), selectinload(Opportunity.values), selectinload(Opportunity.partners))
        if q: statement = statement.where(or_(Pursuit.name.ilike(needle), Company.name.ilike(needle), Pursuit.source_detail.ilike(needle)))
        if owner_id: statement = statement.where(Pursuit.owner_id == owner_id)
        if status: statement = statement.where(Opportunity.stage == status)
        if country: statement = statement.where(func.lower(Company.country) == country.casefold())
        if source: statement = statement.where(Pursuit.source_channel == source)
        if service: statement = statement.where(Opportunity.service_line == service)
        if priority: statement = statement.where(Pursuit.priority == priority)
        if holder_id: statement=statement.where(Pursuit.holder_id==holder_id)
        if blocker: statement=statement.where(Pursuit.blocker==blocker)
        if action_from: statement=statement.where(Pursuit.action_date>=action_from)
        if action_to: statement=statement.where(Pursuit.action_date<=action_to)
        if interaction_from: statement=statement.where(Pursuit.last_client_interaction>=datetime.combine(interaction_from,datetime.min.time(),tzinfo=timezone.utc))
        if interaction_to: statement=statement.where(Pursuit.last_client_interaction<datetime.combine(interaction_to+timedelta(days=1),datetime.min.time(),tzinfo=timezone.utc))
        partner_exists=select(PartnerInvolvement.id).where(PartnerInvolvement.opportunity_id==Opportunity.id,PartnerInvolvement.tenant_id==user.tenant_id,PartnerInvolvement.is_deleted.is_(False)).exists()
        if partner=="yes": statement=statement.where(partner_exists)
        if partner=="no": statement=statement.where(~partner_exists)
        today=date.today()
        if close_period=="overdue": statement=statement.where(Opportunity.expected_close_date<today,Opportunity.stage.notin_(["won","lost"]))
        if close_period=="this_month": start=today.replace(day=1); end=(start.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1); statement=statement.where(Opportunity.expected_close_date.between(start,end))
        if close_period in {"this_quarter","next_quarter"}:
            start=today.replace(month=((today.month-1)//3)*3+1,day=1); month=start.month+(3 if close_period=="next_quarter" else 0); start=start.replace(year=start.year+(month>12),month=((month-1)%12)+1); month=start.month+3; end=start.replace(year=start.year+(month>12),month=((month-1)%12)+1)-timedelta(days=1); statement=statement.where(Opportunity.expected_close_date.between(start,end))
        if close_from: statement=statement.where(Opportunity.expected_close_date>=close_from)
        if close_to: statement=statement.where(Opportunity.expected_close_date<=close_to)
        if value_min is not None or value_max is not None:
            if user.level not in MANAGEMENT:
                assigned=select(TeamRole.id).where(TeamRole.pursuit_id==Pursuit.id,TeamRole.user_id==user.id,TeamRole.is_deleted.is_(False)).exists()
                statement=statement.where(or_(Opportunity.restricted.is_(False),Pursuit.owner_id==user.id,Pursuit.sourced_by_id==user.id,Pursuit.holder_id==user.id,assigned))
            if value_min is not None: statement=statement.where(Opportunity.value_usd>=value_min)
            if value_max is not None: statement=statement.where(Opportunity.value_usd<=value_max)
        columns = {"name": Pursuit.name, "action_date": Pursuit.action_date, "close_date": Opportunity.expected_close_date, "value": Opportunity.value_usd, "created": Pursuit.created_at, "updated": Pursuit.updated_at}
        order = columns.get(sort, Pursuit.updated_at); statement = statement.order_by(order.desc() if descending else order.asc(), Opportunity.id)
        total, items = paginated(db, statement, page, page_size); payload = [out.opportunity(db, item, user) for item in items]
    if export_format: return exported_list(entity_type, payload, export_format)
    pages = max(1, (total + page_size - 1) // page_size)
    return {"entity_type": entity_type, "items": payload, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.post("/pursuits/bulk-assignment/")
def bulk_assignment(payload: BulkAssignmentInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    manager(user); owner = tenant_user(db, user, payload.owner_id); holder = tenant_user(db, user, payload.holder_id)
    statement = scoped(db, Pursuit, user).where(Pursuit.id.in_(payload.pursuit_ids))
    if db.bind and db.bind.dialect.name != "sqlite": statement = statement.with_for_update()
    items = db.scalars(statement).all()
    if len(items) != len(set(payload.pursuit_ids)): raise http_error(404, "One or more pursuits were not found in this workspace.")
    conflicts = [str(item.id) for item in items if payload.versions.get(str(item.id)) != item.version]
    if conflicts: raise http_error(409, {"records": "Some selected pursuits changed. Refresh and select them again.", "ids": conflicts})
    for item in items:
        before = {"owner_id": item.owner_id, "holder_id": item.holder_id, "version": item.version}
        if owner: item.owner_id = owner.id
        if holder and item.holder_id != holder.id: item.holder_id = holder.id; item.ball_since = datetime.now(timezone.utc)
        item.version += 1; item.updated_by_id = user.id
        audit(db, user, "Pursuit bulk assigned", item, payload.reason, before=before, after={"owner_id": item.owner_id, "holder_id": item.holder_id, "version": item.version})
    db.commit()
    return {"detail": "Assignments updated.", "updated": len(items)}


def stakeholder_data(link: PursuitContact) -> dict:
    return {"link_id": str(link.id), "id": str(link.contact_id), "name": link.contact.name, "role": link.role, "job_title": link.contact.job_title, "email": link.contact.email}


def stakeholder_list(db: Session, user: User, pursuit_id: UUID) -> list[dict]:
    links = db.scalars(scoped(db, PursuitContact, user).where(PursuitContact.pursuit_id == pursuit_id).options(selectinload(PursuitContact.contact)).order_by(PursuitContact.role, PursuitContact.created_at)).all()
    return [stakeholder_data(link) for link in links]


@router.post("/pursuits/{pursuit_id}/stakeholders/", status_code=201)
def add_stakeholder(pursuit_id: UUID, payload: StakeholderInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = get_scoped(db, Pursuit, user, pursuit_id); require_work(db, user, pursuit)
    if not db.scalar(scoped(db, Opportunity, user).where(Opportunity.pursuit_id == pursuit.id)): raise http_error(422, "Stakeholder editing is available after lead conversion.")
    contact = get_scoped(db, Contact, user, payload.contact_id)
    if contact.company_id != pursuit.company_id: raise http_error(422, {"contact_id": "Choose a contact at this opportunity's company."})
    existing = db.scalar(scoped(db, PursuitContact, user).where(PursuitContact.pursuit_id == pursuit.id, PursuitContact.contact_id == contact.id))
    if existing: raise http_error(422, {"contact_id": "This contact is already a stakeholder."})
    link = PursuitContact(**stamp(user), pursuit_id=pursuit.id, contact_id=contact.id, role=payload.role)
    db.add(link); audit(db, user, "Stakeholder added", pursuit, f"{contact.name}: {payload.role}"); db.commit()
    return stakeholder_list(db, user, pursuit.id)


@router.patch("/stakeholders/{identifier}/")
def update_stakeholder(identifier: UUID, payload: StakeholderPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    link = db.scalar(scoped(db, PursuitContact, user).where(PursuitContact.id == identifier).options(selectinload(PursuitContact.contact), selectinload(PursuitContact.pursuit)))
    if not link: raise http_error(404, "Stakeholder not found.")
    require_work(db, user, link.pursuit); before = link.role; link.role = payload.role; link.updated_by_id = user.id
    audit(db, user, "Stakeholder role changed", link.pursuit, f"{link.contact.name}: {before} to {payload.role}"); db.commit()
    return stakeholder_list(db, user, link.pursuit_id)


@router.delete("/stakeholders/{identifier}/")
def delete_stakeholder(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    link = db.scalar(scoped(db, PursuitContact, user).where(PursuitContact.id == identifier).options(selectinload(PursuitContact.contact), selectinload(PursuitContact.pursuit)))
    if not link: raise http_error(404, "Stakeholder not found.")
    require_work(db, user, link.pursuit)
    primary = db.scalar(scoped(db, Opportunity, user).where(Opportunity.pursuit_id == link.pursuit_id, Opportunity.primary_contact_id == link.contact_id))
    if primary: raise http_error(422, "The primary contact cannot be removed. Choose another primary contact first.")
    link.is_deleted = True; link.updated_by_id = user.id; audit(db, user, "Stakeholder removed", link.pursuit, link.contact.name); db.commit()
    return stakeholder_list(db, user, link.pursuit_id)
