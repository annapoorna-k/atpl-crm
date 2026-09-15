from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .constants import MANAGEMENT
from .database import get_db
from .models import Artifact, ArtifactRecipient, Contact, Pursuit, TeamRole, User
from .schemas import ArtifactInput, ArtifactLibraryInput, ArtifactReuseInput, ArtifactShareInput
from .security import current_user
from .services import audit, can_value, can_work, get_scoped, http_error, require_work, scoped, stamp, utc
from .settings import Settings, get_settings

router = APIRouter(prefix="/api/v1")

ARTIFACT_TYPES = {
    "Deck", "Proposal", "Case study", "Video", "Demo / POC output",
    "Technical architecture", "Pricing", "NDA", "SOW", "Contract",
    "Purchase order", "Customer document", "Email", "Other",
}
EMAIL_CLASSIFICATIONS = {
    "Customer communication", "Internal approval", "Proposal sent",
    "Technical information", "Other",
}
SAFE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt",
    ".csv", ".png", ".jpg", ".jpeg", ".gif", ".msg", ".eml", ".mp4",
}


def load_pursuit(db: Session, user: User, identifier: UUID) -> Pursuit:
    item = db.scalar(scoped(db, Pursuit, user).where(Pursuit.id == identifier).options(selectinload(Pursuit.opportunity)))
    if not item:
        raise http_error(404, "Record not found.")
    if item.opportunity and not can_value(db, user, item.opportunity):
        raise http_error(404, "Record not found.")
    return item


def artifact_options():
    return (
        selectinload(Artifact.pursuit), selectinload(Artifact.company),
        selectinload(Artifact.approved_by),
        selectinload(Artifact.recipients).selectinload(ArtifactRecipient.contact),
    )


def load_artifact(db: Session, user: User, identifier: UUID) -> Artifact:
    item = db.scalar(scoped(db, Artifact, user).where(Artifact.id == identifier).options(*artifact_options()))
    if not item:
        raise http_error(404, "Artifact not found.")
    pursuit = load_pursuit(db, user, item.pursuit_id)
    if item.internal_only and not can_work(db, user, pursuit):
        raise http_error(404, "Artifact not found.")
    return item


def artifact_type(value: str) -> str:
    if value not in ARTIFACT_TYPES:
        raise http_error(422, {"artifact_type": "Choose a supported artifact type."})
    return value


def safe_name(filename: str) -> str:
    value = Path(filename or "attachment").name
    return re.sub(r"[^A-Za-z0-9._ -]", "_", value)[:255] or "attachment"


async def store_upload(upload: UploadFile, artifact_id: UUID, tenant_id: UUID, settings: Settings) -> dict:
    filename = safe_name(upload.filename or "attachment")
    extension = Path(filename).suffix.casefold()
    if extension not in SAFE_EXTENSIONS:
        raise http_error(422, {"file": "This file type is not allowed. Upload a standard document, image, email or MP4 file."})
    maximum = settings.artifact_max_upload_mb * 1024 * 1024
    digest = hashlib.sha256()
    size = 0
    directory = Path(settings.artifact_storage_root) / str(tenant_id)
    directory.mkdir(parents=True, exist_ok=True)
    storage_key = f"{artifact_id}{extension}"
    target = directory / storage_key
    try:
        with target.open("wb") as handle:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > maximum:
                    raise http_error(413, f"Files are limited to {settings.artifact_max_upload_mb} MB.")
                digest.update(chunk)
                handle.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if not size:
        target.unlink(missing_ok=True)
        raise http_error(422, {"file": "The uploaded file is empty."})
    return {
        "storage_key": storage_key, "original_filename": filename,
        "content_type": (upload.content_type or "application/octet-stream")[:150],
        "byte_size": size, "checksum_sha256": digest.hexdigest(),
    }


def recipient_contacts(db: Session, user: User, pursuit: Pursuit, identifiers: list[UUID]) -> list[Contact]:
    unique = list(dict.fromkeys(identifiers))
    if not unique:
        raise http_error(422, {"contact_ids": "Select at least one client contact."})
    contacts = list(db.scalars(scoped(db, Contact, user).where(Contact.id.in_(unique), Contact.company_id == pursuit.company_id)).all())
    if len(contacts) != len(unique):
        raise http_error(422, {"contact_ids": "Every recipient must be a contact at this pursuit's company."})
    return contacts


def attach_recipients(db: Session, user: User, artifact: Artifact, contacts: list[Contact]) -> None:
    existing = {row.contact_id for row in artifact.recipients if not row.is_deleted}
    for contact in contacts:
        if contact.id not in existing:
            db.add(ArtifactRecipient(**stamp(user), artifact_id=artifact.id, contact_id=contact.id))


def is_superseded(db: Session, user: User, item: Artifact) -> bool:
    return bool(db.scalar(scoped(db, Artifact, user).where(Artifact.supersedes_id == item.id).with_only_columns(Artifact.id).limit(1)))


def present(db: Session, user: User, item: Artifact) -> dict:
    return {
        "id": str(item.id), "pursuit_id": str(item.pursuit_id), "pursuit": item.pursuit.name,
        "company_id": str(item.company_id), "company": item.company.name, "title": item.title,
        "artifact_type": item.artifact_type, "kind": item.kind,
        "url": (item.storage_link if item.kind != "Linked email" or item.storage_link.startswith(("https://", "http://")) else "") or (f"/api/v1/artifacts/{item.id}/download/" if item.storage_key else ""),
        "original_filename": item.original_filename, "content_type": item.content_type,
        "byte_size": item.byte_size, "checksum_sha256": item.checksum_sha256,
        "version": item.version, "supersedes_id": str(item.supersedes_id) if item.supersedes_id else None,
        "superseded": is_superseded(db, user, item), "parent_email_id": str(item.parent_email_id) if item.parent_email_id else None,
        "email_classification": item.email_classification, "message_reference": item.message_reference,
        "email_subject": item.email_subject, "email_date": item.email_date,
        "email_direction": item.email_direction, "email_participants": item.email_participants,
        "internal_only": item.internal_only, "is_reusable": item.is_reusable,
        "approved": bool(item.approved_by_id), "approved_by": item.approved_by.display_name if item.approved_by else None,
        "approved_at": item.approved_at, "shared_with_client": item.shared_with_client,
        "shared_at": item.shared_at,
        "recipients": [{"id": str(row.contact_id), "name": row.contact.name, "email": row.contact.email} for row in item.recipients if not row.is_deleted],
        "created_at": item.created_at,
    }


def visible_statement(db: Session, user: User):
    statement = scoped(db, Artifact, user).options(*artifact_options())
    if user.level not in MANAGEMENT:
        own_pursuits = select(Pursuit.id).where(Pursuit.tenant_id == user.tenant_id, Pursuit.is_deleted.is_(False)).where(
            or_(Pursuit.owner_id == user.id, Pursuit.holder_id == user.id, Pursuit.id.in_(select(TeamRole.pursuit_id).where(TeamRole.tenant_id == user.tenant_id, TeamRole.user_id == user.id, TeamRole.is_deleted.is_(False))))
        )
        statement = statement.where(or_(Artifact.internal_only.is_(False), Artifact.pursuit_id.in_(own_pursuits)))
    return statement


@router.get("/artifacts/")
def list_artifacts(
    search: str = "", pursuit_id: UUID | None = None, company_id: UUID | None = None,
    shared_only: bool = False, reusable_only: bool = False, include_superseded: bool = True,
    db: Session = Depends(get_db), user: User = Depends(current_user),
):
    statement = visible_statement(db, user)
    if pursuit_id: statement = statement.where(Artifact.pursuit_id == pursuit_id)
    if company_id: statement = statement.where(Artifact.company_id == company_id)
    if shared_only: statement = statement.where(Artifact.shared_with_client.is_(True))
    if reusable_only: statement = statement.where(Artifact.is_reusable.is_(True))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Artifact.title.ilike(term), Artifact.artifact_type.ilike(term), Artifact.email_subject.ilike(term), Artifact.original_filename.ilike(term)))
    rows = list(db.scalars(statement.order_by(Artifact.shared_at.desc().nullslast(), Artifact.created_at.desc()).limit(500)).unique().all())
    data = [present(db, user, item) for item in rows]
    if not include_superseded: data = [item for item in data if not item["superseded"]]
    return data


@router.get("/artifacts/register/")
def shared_register(search: str = "", pursuit_id: UUID | None = None, company_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list_artifacts(search, pursuit_id, company_id, True, False, True, db, user)


@router.get("/artifacts/library/")
def asset_library(search: str = "", db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list_artifacts(search, None, None, False, True, False, db, user)


@router.get("/artifacts/{identifier}/download/")
def download_artifact(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings)):
    item = load_artifact(db, user, identifier)
    if not item.storage_key:
        raise http_error(404, "This artifact does not contain a managed file.")
    path = Path(settings.artifact_storage_root) / str(user.tenant_id) / item.storage_key
    if not path.is_file():
        raise http_error(404, "The managed file is unavailable.")
    return FileResponse(path, media_type=item.content_type or "application/octet-stream", filename=item.original_filename)


@router.post("/artifacts/", status_code=201)
@router.post("/artifacts/links/", status_code=201)
def create_link(payload: ArtifactInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pursuit = load_pursuit(db, user, payload.pursuit); require_work(db, user, pursuit)
    item = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit.id, company_id=pursuit.company_id, title=payload.title,
                    artifact_type=artifact_type(payload.artifact_type), kind="SharePoint / OneDrive link",
                    storage_link=str(payload.storage_link), internal_only=payload.internal_only, is_reusable=payload.is_reusable)
    db.add(item); audit(db, user, "Artifact linked", pursuit, item.title); db.commit(); db.refresh(item)
    return {"id": str(item.id)}


@router.post("/artifacts/uploads/", status_code=201)
async def create_upload(
    pursuit: UUID = Form(), title: str = Form(min_length=1, max_length=180), artifact_type_value: str = Form(alias="artifact_type"),
    internal_only: bool = Form(False), is_reusable: bool = Form(False), file: UploadFile = File(),
    db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings),
):
    pursuit_row = load_pursuit(db, user, pursuit); require_work(db, user, pursuit_row)
    item = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit_row.id, company_id=pursuit_row.company_id, title=title,
                    artifact_type=artifact_type(artifact_type_value), kind="Uploaded file", internal_only=internal_only, is_reusable=is_reusable)
    values = await store_upload(file, item.id, user.tenant_id, settings)
    for key, value in values.items(): setattr(item, key, value)
    try:
        db.add(item); audit(db, user, "Artifact uploaded", pursuit_row, item.title); db.commit()
    except Exception:
        (Path(settings.artifact_storage_root) / str(user.tenant_id) / item.storage_key).unlink(missing_ok=True)
        raise
    return {"id": str(item.id)}


def parse_ids(value: str, field: str) -> list[UUID]:
    try:
        raw = json.loads(value or "[]")
        return [UUID(item) for item in raw]
    except (ValueError, TypeError, json.JSONDecodeError):
        raise http_error(422, {field: "Provide a valid list."})


@router.post("/artifacts/emails/", status_code=201)
async def link_email(
    pursuit: UUID = Form(), subject: str = Form(min_length=1, max_length=250), message_reference: str = Form(min_length=1, max_length=500),
    email_date: datetime = Form(), direction: str = Form(), participants: str = Form(), classification: str = Form(),
    recipient_contact_ids: str = Form("[]"), internal_only: bool = Form(False), attachments: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings),
):
    pursuit_row = load_pursuit(db, user, pursuit); require_work(db, user, pursuit_row)
    if direction not in {"Inbound", "Outbound"}: raise http_error(422, {"direction": "Choose Inbound or Outbound."})
    if classification not in EMAIL_CLASSIFICATIONS: raise http_error(422, {"classification": "Choose a supported email classification."})
    try:
        people = [str(value).strip().lower() for value in json.loads(participants) if str(value).strip()]
    except (TypeError, json.JSONDecodeError):
        raise http_error(422, {"participants": "Provide a valid participant list."})
    if not people: raise http_error(422, {"participants": "Record at least one email participant."})
    contact_ids = parse_ids(recipient_contact_ids, "recipient_contact_ids")
    contacts = recipient_contacts(db, user, pursuit_row, contact_ids) if direction == "Outbound" and not internal_only else []
    shared_at = utc(email_date) if direction == "Outbound" and contacts and not internal_only else None
    email = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit_row.id, company_id=pursuit_row.company_id, title=subject,
                     artifact_type="Email", kind="Linked email", storage_link=message_reference,
                     email_classification=classification, message_reference=message_reference, email_subject=subject,
                     email_date=email_date, email_direction=direction, email_participants=people,
                     internal_only=internal_only, approved_by_id=user.id, approved_at=datetime.now(timezone.utc),
                     shared_with_client=bool(shared_at), shared_at=shared_at)
    db.add(email); attach_recipients(db, user, email, contacts)
    created_files: list[str] = []
    child_ids: list[str] = []
    try:
        for upload in attachments:
            child = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit_row.id, company_id=pursuit_row.company_id,
                             title=safe_name(upload.filename or "Email attachment"), artifact_type=infer_artifact_type(upload.filename or ""),
                             kind="Uploaded file", parent_email_id=email.id, internal_only=internal_only,
                             approved_by_id=user.id, approved_at=email.approved_at,
                             shared_with_client=bool(shared_at), shared_at=shared_at)
            values = await store_upload(upload, child.id, user.tenant_id, settings)
            for key, value in values.items(): setattr(child, key, value)
            created_files.append(child.storage_key); child_ids.append(str(child.id)); db.add(child); attach_recipients(db, user, child, contacts)
        audit(db, user, "Email linked", pursuit_row, f"{subject} · {classification} · {len(child_ids)} attachment(s)")
        db.commit()
    except Exception:
        db.rollback()
        for key in created_files: (Path(settings.artifact_storage_root) / str(user.tenant_id) / key).unlink(missing_ok=True)
        raise
    return {"id": str(email.id), "attachment_ids": child_ids}


def infer_artifact_type(filename: str) -> str:
    value = filename.casefold()
    if "proposal" in value: return "Proposal"
    if "pricing" in value or "quote" in value: return "Pricing"
    if "sow" in value or "statement of work" in value: return "SOW"
    if "contract" in value: return "Contract"
    if "nda" in value: return "NDA"
    if Path(value).suffix in {".ppt", ".pptx"}: return "Deck"
    return "Customer document"


@router.post("/artifacts/{identifier}/approve/")
def approve_artifact(identifier: UUID, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.level not in MANAGEMENT: raise http_error(403, "Management approval is required before client sharing.")
    item = load_artifact(db, user, identifier); pursuit = load_pursuit(db, user, item.pursuit_id)
    if item.internal_only: raise http_error(422, "An internal-only artifact cannot be approved for client sharing.")
    if is_superseded(db, user, item): raise http_error(422, "Approve the current version instead of a superseded version.")
    item.approved_by_id, item.approved_at, item.updated_by_id = user.id, datetime.now(timezone.utc), user.id
    audit(db, user, "Artifact approved", pursuit, f"{item.title} v{item.version}"); db.commit()
    return {"detail": "Artifact approved for client sharing."}


@router.post("/artifacts/{identifier}/share/")
def share_artifact(identifier: UUID, payload: ArtifactShareInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = load_artifact(db, user, identifier); pursuit = load_pursuit(db, user, item.pursuit_id); require_work(db, user, pursuit)
    if item.internal_only: raise http_error(422, "An internal-only artifact cannot be shared with a client.")
    if not item.approved_by_id: raise http_error(422, "Management approval is required before client sharing.")
    if is_superseded(db, user, item): raise http_error(422, "Share the current version instead of a superseded version.")
    contacts = recipient_contacts(db, user, pursuit, payload.contact_ids)
    attach_recipients(db, user, item, contacts)
    item.shared_with_client, item.shared_at, item.updated_by_id = True, payload.shared_at or datetime.now(timezone.utc), user.id
    audit(db, user, "Artifact shared", pursuit, f"{item.title} v{item.version} · {', '.join(contact.name for contact in contacts)}")
    db.commit(); return {"detail": "Client-shared register updated."}


@router.post("/artifacts/{identifier}/library/")
def set_library(identifier: UUID, payload: ArtifactLibraryInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = load_artifact(db, user, identifier); pursuit = load_pursuit(db, user, item.pursuit_id); require_work(db, user, pursuit)
    item.is_reusable, item.updated_by_id = payload.enabled, user.id
    audit(db, user, "Asset library updated", pursuit, f"{item.title}: {'included' if payload.enabled else 'removed'}")
    db.commit(); return {"detail": "Reusable asset library updated."}


@router.post("/artifacts/{identifier}/reuse/", status_code=201)
def reuse_artifact(identifier: UUID, payload: ArtifactReuseInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    source = load_artifact(db, user, identifier)
    if not source.is_reusable or source.kind == "Linked email": raise http_error(422, "Choose a reusable file or link from the library.")
    pursuit = load_pursuit(db, user, payload.pursuit); require_work(db, user, pursuit)
    item = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit.id, company_id=pursuit.company_id, title=payload.title or source.title,
                    artifact_type=source.artifact_type, kind=source.kind, storage_link=source.storage_link,
                    storage_key=source.storage_key, original_filename=source.original_filename, content_type=source.content_type,
                    byte_size=source.byte_size, checksum_sha256=source.checksum_sha256, source_artifact_id=source.id)
    db.add(item); audit(db, user, "Reusable asset attached", pursuit, item.title); db.commit(); return {"id": str(item.id)}


@router.post("/artifacts/{identifier}/versions/link/", status_code=201)
def new_link_version(identifier: UUID, payload: ArtifactInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    previous = load_artifact(db, user, identifier); pursuit = load_pursuit(db, user, previous.pursuit_id); require_work(db, user, pursuit)
    if payload.pursuit != pursuit.id: raise http_error(422, {"pursuit": "A new version must remain on the same pursuit."})
    if is_superseded(db, user, previous): raise http_error(409, "This version has already been superseded. Refresh and use the current version.")
    item = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit.id, company_id=pursuit.company_id, title=payload.title,
                    artifact_type=artifact_type(payload.artifact_type), kind="SharePoint / OneDrive link", storage_link=str(payload.storage_link),
                    version=previous.version + 1, supersedes_id=previous.id, internal_only=payload.internal_only, is_reusable=payload.is_reusable)
    db.add(item); audit(db, user, "Artifact version added", pursuit, f"{item.title} v{item.version}"); db.commit(); return {"id": str(item.id)}


@router.post("/artifacts/{identifier}/versions/upload/", status_code=201)
async def new_upload_version(
    identifier: UUID, title: str = Form(min_length=1, max_length=180), artifact_type_value: str = Form(alias="artifact_type"),
    internal_only: bool = Form(False), is_reusable: bool = Form(False), file: UploadFile = File(),
    db: Session = Depends(get_db), user: User = Depends(current_user), settings: Settings = Depends(get_settings),
):
    previous = load_artifact(db, user, identifier); pursuit = load_pursuit(db, user, previous.pursuit_id); require_work(db, user, pursuit)
    if is_superseded(db, user, previous): raise http_error(409, "This version has already been superseded. Refresh and use the current version.")
    item = Artifact(id=uuid.uuid4(), **stamp(user), pursuit_id=pursuit.id, company_id=pursuit.company_id, title=title,
                    artifact_type=artifact_type(artifact_type_value), kind="Uploaded file", version=previous.version + 1,
                    supersedes_id=previous.id, internal_only=internal_only, is_reusable=is_reusable)
    values = await store_upload(file, item.id, user.tenant_id, settings)
    for key, value in values.items(): setattr(item, key, value)
    try:
        db.add(item); audit(db, user, "Artifact version added", pursuit, f"{item.title} v{item.version}"); db.commit()
    except Exception:
        (Path(settings.artifact_storage_root) / str(user.tenant_id) / item.storage_key).unlink(missing_ok=True); raise
    return {"id": str(item.id)}
