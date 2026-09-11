from uuid import UUID
from fastapi import APIRouter, Depends
from pwdlib import PasswordHash
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from . import presenters as out
from .constants import LOCKED_REFERENCE_CATEGORIES, REFERENCE_DEFAULTS
from .database import get_db
from .models import AppSession, ExchangeRate, User, WorkspaceReference
from .schemas import AdminUserInput, AdminUserPatch, RatePatch, ReferenceInput, ReferencePatch
from .security import current_user
from .services import audit, get_scoped, http_error, stamp

router = APIRouter(prefix="/api/v1/admin", tags=["administration"])
passwords = PasswordHash.recommended()

def administrator(user: User = Depends(current_user)) -> User:
    if user.level != "Administrator": raise http_error(403, "Workspace Administrator access is required.")
    return user

def reference_out(item: WorkspaceReference) -> dict:
    return {"id": str(item.id), "category": item.category, "code": item.code, "label": item.label, "numeric_value": item.numeric_value, "sort_order": item.sort_order, "active": item.active, "locked": item.category in LOCKED_REFERENCE_CATEGORIES}

@router.post("/users/", status_code=201)
def create_user(payload: AdminUserInput, db: Session = Depends(get_db), admin: User = Depends(administrator)):
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(func.lower(User.username) == email)): raise http_error(422, {"email": "A user with this email already exists."})
    item = User(username=email, email=email, password=passwords.hash(payload.password), first_name=payload.first_name, last_name=payload.last_name, job_title=payload.job_title, level=payload.level, tenant_id=admin.tenant_id, is_active=True)
    db.add(item); audit(db, admin, "Workspace user created", detail=f"{item.display_name} · {item.level}"); db.commit(); db.refresh(item)
    return out.person(item)

@router.patch("/users/{identifier}/")
def update_user(identifier: int, payload: AdminUserPatch, db: Session = Depends(get_db), admin: User = Depends(administrator)):
    item = db.scalar(select(User).where(User.id == identifier, User.tenant_id == admin.tenant_id))
    if not item: raise http_error(404, "User not found.")
    values = payload.model_dump(exclude_unset=True)
    if item.id == admin.id and (values.get("is_active") is False or ("level" in values and values["level"] != "Administrator")): raise http_error(422, "You cannot deactivate or remove your own Administrator access.")
    if "email" in values:
        email = str(values.pop("email")).lower(); duplicate = db.scalar(select(User.id).where(func.lower(User.username) == email, User.id != item.id))
        if duplicate: raise http_error(422, {"email": "A user with this email already exists."})
        item.email = item.username = email
    password = values.pop("password", None); before = {"name": item.display_name, "level": item.level, "active": item.is_active}
    for key, value in values.items(): setattr(item, key, value)
    if password: item.password = passwords.hash(password)
    if values.get("is_active") is False or password: db.execute(delete(AppSession).where(AppSession.user_id == item.id))
    audit(db, admin, "Workspace user updated", detail=item.display_name, before=before, after={"name": item.display_name, "level": item.level, "active": item.is_active}); db.commit(); db.refresh(item)
    return out.person(item)

@router.post("/references/", status_code=201)
def create_reference(payload: ReferenceInput, db: Session = Depends(get_db), admin: User = Depends(administrator)):
    if payload.category not in REFERENCE_DEFAULTS: raise http_error(422, {"category": "Choose a supported reference category."})
    if payload.category in LOCKED_REFERENCE_CATEGORIES: raise http_error(422, "Workflow codes are fixed; edit their label, order, active state or probability.")
    if db.scalar(select(WorkspaceReference.id).where(WorkspaceReference.tenant_id == admin.tenant_id, WorkspaceReference.category == payload.category, func.lower(WorkspaceReference.code) == payload.code.lower())): raise http_error(422, {"code": "This code already exists in the category."})
    item = WorkspaceReference(**stamp(admin), **payload.model_dump()); db.add(item); audit(db, admin, "Reference option created", detail=f"{item.category}: {item.label}"); db.commit(); db.refresh(item)
    return reference_out(item)

@router.patch("/references/{identifier}/")
def update_reference(identifier: UUID, payload: ReferencePatch, db: Session = Depends(get_db), admin: User = Depends(administrator)):
    item = get_scoped(db, WorkspaceReference, admin, identifier); values = payload.model_dump(exclude_unset=True)
    if item.category == "stages" and "numeric_value" in values and values["numeric_value"] is None: raise http_error(422, {"numeric_value": "A stage probability is required."})
    if item.category == "blockers" and item.code == "None" and values.get("active") is False: raise http_error(422, "The default None blocker must remain active.")
    before = {"label": item.label, "numeric_value": item.numeric_value, "sort_order": item.sort_order, "active": item.active}
    for key, value in values.items(): setattr(item, key, value)
    item.updated_by_id = admin.id; audit(db, admin, "Reference option updated", detail=f"{item.category}: {item.code}", before=before, after=values); db.commit(); db.refresh(item)
    return reference_out(item)

@router.patch("/rates/{identifier}/")
def update_rate(identifier: UUID, payload: RatePatch, db: Session = Depends(get_db), admin: User = Depends(administrator)):
    item = get_scoped(db, ExchangeRate, admin, identifier)
    if item.currency == "USD" and payload.rate != 1: raise http_error(422, {"rate": "USD is the reporting base and must remain 1."})
    before = {"rate": str(item.rate), "source": item.source}; item.rate, item.source, item.updated_by_id = payload.rate, payload.source, admin.id
    audit(db, admin, "Exchange rate updated", detail=item.currency, before=before, after={"rate": str(payload.rate), "source": payload.source}); db.commit(); db.refresh(item)
    return {"id": str(item.id), "currency": item.currency, "rate": str(item.rate), "source": item.source}
