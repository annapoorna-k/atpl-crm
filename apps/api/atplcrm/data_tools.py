"""Tenant-scoped imports, search, duplicate review and data-quality endpoints."""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from .constants import MANAGEMENT
from .database import get_db
from .models import Activity, Company, Contact, ImportJob, Lead, Opportunity, Pursuit, PursuitContact, User
from .references import require_code
from .schemas import ImportInput, MergeInput
from .security import current_user
from .services import audit, future_date, http_error, scoped, stamp

router = APIRouter(prefix="/api/v1/data", tags=["data tools"])

TEMPLATES = {
    "companies": ["name", "country", "owner_email", "domain", "industry", "company_type", "primary_region", "global_account_name"],
    "contacts": ["company_name", "first_name", "last_name", "country", "owner_email", "email", "job_title", "phone", "mobile", "city", "source_channel"],
    "leads": ["name", "company_name", "owner_email", "next_action", "action_type", "action_date", "source_channel", "source_detail", "priority", "area_of_interest"],
}
REQUIRED = {
    "companies": {"name", "country", "owner_email"},
    "contacts": {"company_name", "first_name", "last_name", "country", "owner_email"},
    "leads": {"name", "company_name", "owner_email", "next_action", "action_type", "action_date", "source_channel"},
}


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def import_access(user: User) -> None:
    if user.level not in MANAGEMENT:
        raise http_error(403, "Manager, Executive or Administrator access is required for imports and merges.")


def parse(payload: ImportInput) -> tuple[list[str], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.csv_text.lstrip("\ufeff")))
        headers = [str(value).strip() for value in (reader.fieldnames or []) if value]
        rows = [{str(k).strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]
    except csv.Error as exc:
        raise http_error(422, {"csv_text": f"Could not read this CSV: {exc}"}) from exc
    if not headers:
        raise http_error(422, {"csv_text": "The CSV needs a header row."})
    if len(rows) > 5000:
        raise http_error(422, {"csv_text": "A single import can contain at most 5,000 rows."})
    return headers, rows


def source_for(field: str, headers: list[str], mapping: dict[str, str]) -> str | None:
    requested = mapping.get(field, field)
    by_normalized = {normalized(header): header for header in headers}
    return by_normalized.get(normalized(requested))


def canonical_rows(payload: ImportInput) -> tuple[list[str], list[dict[str, str]], list[str]]:
    headers, raw = parse(payload)
    fields = TEMPLATES[payload.entity_type]
    sources = {field: source_for(field, headers, payload.mapping) for field in fields}
    missing = sorted(field for field in REQUIRED[payload.entity_type] if not sources[field])
    rows = [{field: row.get(source, "") if source else "" for field, source in sources.items()} for row in raw]
    return headers, rows, missing


def tenant_user(db: Session, user: User, email: str) -> User | None:
    return db.scalar(select(User).where(User.tenant_id == user.tenant_id, User.is_active.is_(True), func.lower(User.email) == email.casefold()))


def tenant_company(db: Session, user: User, name: str) -> Company | None:
    return db.scalar(scoped(db, Company, user).where(func.lower(Company.name) == name.casefold()))


def row_errors(db: Session, user: User, entity: str, row: dict[str, str], number: int) -> list[dict]:
    errors: list[dict] = []
    for field in REQUIRED[entity]:
        if not row.get(field):
            errors.append({"row": number, "field": field, "message": "Required value is missing."})
    if errors:
        return errors
    owner = tenant_user(db, user, row["owner_email"])
    if not owner:
        errors.append({"row": number, "field": "owner_email", "message": "No active workspace user has this email."})
    if entity == "companies":
        if tenant_company(db, user, row["name"]):
            errors.append({"row": number, "field": "name", "message": "Company already exists."})
    elif entity == "contacts":
        if not tenant_company(db, user, row["company_name"]):
            errors.append({"row": number, "field": "company_name", "message": "Company does not exist. Import companies first."})
        if row.get("email"):
            try:
                validate_email(row["email"], check_deliverability=False)
            except EmailNotValidError:
                errors.append({"row": number, "field": "email", "message": "Enter a valid email address."})
            if db.scalar(scoped(db, Contact, user).where(func.lower(Contact.email) == row["email"].casefold())):
                errors.append({"row": number, "field": "email", "message": "Contact email already exists."})
    else:
        company = tenant_company(db, user, row["company_name"])
        if not company:
            errors.append({"row": number, "field": "company_name", "message": "Company does not exist. Import companies first."})
        else:
            duplicate = db.scalar(scoped(db, Pursuit, user).where(Pursuit.company_id == company.id, func.lower(Pursuit.name) == row["name"].casefold()))
            if duplicate:
                errors.append({"row": number, "field": "name", "message": "A pursuit with this name already exists at the company."})
        try:
            parsed = date.fromisoformat(row["action_date"])
            if parsed <= date.today():
                errors.append({"row": number, "field": "action_date", "message": "Use a date after today (YYYY-MM-DD)."})
        except ValueError:
            errors.append({"row": number, "field": "action_date", "message": "Use YYYY-MM-DD format."})
        for category, field in (("actions", "action_type"), ("sources", "source_channel")):
            try:
                require_code(db, user, category, row[field], field)
            except Exception:
                errors.append({"row": number, "field": field, "message": "Value is not active in workspace configuration."})
    return errors


@router.get("/templates/{entity_type}/")
def template(entity_type: str, user: User = Depends(current_user)):
    if entity_type not in TEMPLATES:
        raise http_error(404, "Import template not found.")
    example = {
        "companies": ["Example Industries", "United States", user.email, "example.com", "Manufacturing", "Prospect", "North America", ""],
        "contacts": ["Example Industries", "Avery", "Stone", "United States", user.email, "avery@example.com", "Director", "+1 555 0100", "", "Austin", "LinkedIn"],
        "leads": ["Analytics modernization", "Example Industries", user.email, "Confirm discovery call", "Call", str(date.today().replace(year=date.today().year + 1)), "LinkedIn", "Direct outreach", "Medium", "Analytics"],
    }[entity_type]
    stream = io.StringIO(); writer = csv.writer(stream); writer.writerow(TEMPLATES[entity_type]); writer.writerow(example)
    return {"entity_type": entity_type, "filename": f"atplcrm-{entity_type}-template.csv", "csv_text": stream.getvalue(), "required": sorted(REQUIRED[entity_type])}


@router.post("/imports/preview/")
def preview_import(payload: ImportInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    import_access(user)
    headers, rows, missing = canonical_rows(payload)
    errors = [{"row": 1, "field": field, "message": "Map this required field to a CSV column."} for field in missing]
    if not missing:
        for number, row in enumerate(rows, start=2):
            errors.extend(row_errors(db, user, payload.entity_type, row, number))
    invalid_rows = {error["row"] for error in errors if error["row"] > 1}
    return {"headers": headers, "suggested_mapping": {field: source_for(field, headers, payload.mapping) for field in TEMPLATES[payload.entity_type]}, "sample": rows[:5], "total_rows": len(rows), "valid_rows": max(0, len(rows) - len(invalid_rows)) if not missing else 0, "invalid_rows": len(invalid_rows), "errors": errors[:200], "truncated_errors": len(errors) > 200}


@router.post("/imports/", status_code=201)
def execute_import(payload: ImportInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    import_access(user)
    _headers, rows, missing = canonical_rows(payload)
    if missing:
        raise http_error(422, {field: "Map this required field to a CSV column." for field in missing})
    errors: list[dict] = []
    imported = 0
    for number, row in enumerate(rows, start=2):
        found = row_errors(db, user, payload.entity_type, row, number)
        if found:
            errors.extend(found); continue
        owner = tenant_user(db, user, row["owner_email"])
        if payload.entity_type == "companies":
            db.add(Company(**stamp(user), name=row["name"], country=row["country"], owner_id=owner.id, domain=row["domain"].casefold(), industry=row["industry"], company_type=row["company_type"] or "Prospect", primary_region=row["primary_region"], global_account_name=row["global_account_name"]))
        elif payload.entity_type == "contacts":
            company = tenant_company(db, user, row["company_name"])
            db.add(Contact(**stamp(user), company_id=company.id, first_name=row["first_name"], last_name=row["last_name"], country=row["country"], owner_id=owner.id, sourced_by_id=user.id, email=row["email"].casefold(), job_title=row["job_title"], phone=row["phone"], mobile=row["mobile"], city=row["city"], source_channel=row["source_channel"] or "Other"))
        else:
            company = tenant_company(db, user, row["company_name"])
            pursuit = Pursuit(**stamp(user), name=row["name"], company_id=company.id, owner_id=owner.id, sourced_by_id=user.id, holder_id=owner.id, next_action=row["next_action"], action_type=row["action_type"], action_date=date.fromisoformat(row["action_date"]), source_channel=row["source_channel"], source_detail=row["source_detail"], priority=row["priority"] or "Medium")
            db.add(pursuit); db.flush(); db.add(Lead(**stamp(user), pursuit_id=pursuit.id, area_of_interest=row["area_of_interest"]))
        db.flush(); imported += 1
    status = "Completed" if not errors else ("Failed" if not imported else "Completed with errors")
    job = ImportJob(**stamp(user), filename=payload.filename, entity_type=payload.entity_type, status=status, total_rows=len(rows), imported_rows=imported, skipped_rows=len(rows) - imported, errors=errors[:500])
    db.add(job); audit(db, user, "CSV import completed", detail=f"{payload.entity_type}: {imported}/{len(rows)} rows from {payload.filename}"); db.commit(); db.refresh(job)
    return present_job(job)


def present_job(job: ImportJob) -> dict:
    return {"id": str(job.id), "filename": job.filename, "entity_type": job.entity_type, "status": job.status, "total_rows": job.total_rows, "imported_rows": job.imported_rows, "skipped_rows": job.skipped_rows, "errors": job.errors, "created_at": job.created_at, "created_by_id": job.created_by_id}


@router.get("/imports/")
def import_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    jobs = db.scalars(scoped(db, ImportJob, user).order_by(ImportJob.created_at.desc()).limit(50)).all()
    return [present_job(job) for job in jobs]


@router.get("/search/")
def global_search(q: str = Query(min_length=2, max_length=120), entity_type: str = "all", owner_id: int | None = None, status_filter: str = "", country: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(current_user)):
    needle = f"%{q.strip()}%"; results: list[dict] = []
    if entity_type in {"all", "companies"}:
        statement = scoped(db, Company, user).where(or_(Company.name.ilike(needle), Company.domain.ilike(needle), Company.industry.ilike(needle))).options(selectinload(Company.owner))
        if owner_id: statement = statement.where(Company.owner_id == owner_id)
        if country: statement = statement.where(func.lower(Company.country) == country.casefold())
        for item in db.scalars(statement.limit(200)).all(): results.append({"type": "Company", "id": str(item.id), "title": item.name, "subtitle": item.domain or item.industry or item.country, "status": item.company_type, "owner": item.owner.display_name, "route": "companies"})
    if entity_type in {"all", "contacts"}:
        statement = scoped(db, Contact, user).where(or_(Contact.first_name.ilike(needle), Contact.last_name.ilike(needle), Contact.email.ilike(needle), Contact.phone.ilike(needle), Contact.mobile.ilike(needle))).options(selectinload(Contact.company), selectinload(Contact.owner))
        if owner_id: statement = statement.where(Contact.owner_id == owner_id)
        if country: statement = statement.where(func.lower(Contact.country) == country.casefold())
        for item in db.scalars(statement.limit(200)).all(): results.append({"type": "Contact", "id": str(item.id), "title": item.name, "subtitle": f"{item.company.name} · {item.email or item.phone or item.country}", "status": item.engagement_status, "owner": item.owner.display_name, "route": "contacts"})
    if entity_type in {"all", "leads", "opportunities"}:
        statement = scoped(db, Pursuit, user).where(or_(Pursuit.name.ilike(needle), Pursuit.source_detail.ilike(needle))).options(selectinload(Pursuit.company), selectinload(Pursuit.owner), selectinload(Pursuit.lead), selectinload(Pursuit.opportunity))
        if owner_id: statement = statement.where(Pursuit.owner_id == owner_id)
        for item in db.scalars(statement.limit(300)).all():
            kind = "Opportunity" if item.opportunity else "Lead"
            expected_type = "opportunities" if kind == "Opportunity" else "leads"
            if entity_type != "all" and entity_type != expected_type: continue
            state = item.opportunity.stage if item.opportunity else item.lead.status
            if status_filter and state != status_filter: continue
            if country and item.company.country.casefold() != country.casefold(): continue
            results.append({"type": kind, "id": str(item.id), "title": item.name, "subtitle": item.company.name, "status": state, "owner": item.owner.display_name, "route": "pipeline" if item.opportunity else "leads"})
    order = {"Opportunity": 0, "Lead": 1, "Company": 2, "Contact": 3}
    results.sort(key=lambda item: (order[item["type"]], item["title"].casefold()))
    total = len(results); start = (page - 1) * page_size
    return {"query": q, "total": total, "page": page, "page_size": page_size, "results": results[start:start + page_size]}


def duplicate_groups(db: Session, user: User) -> list[dict]:
    groups: list[dict] = []
    companies = db.scalars(scoped(db, Company, user)).all()
    for match_type, getter in (("Company name", lambda item: normalized(item.name)), ("Company domain", lambda item: normalized(item.domain))):
        buckets: dict[str, list[Company]] = defaultdict(list)
        for item in companies:
            key = getter(item)
            if key: buckets[key].append(item)
        for key, items in buckets.items():
            if len(items) > 1: groups.append({"entity_type": "companies", "match_type": match_type, "match_value": key, "records": [{"id": str(item.id), "name": item.name, "detail": item.domain or item.country} for item in items]})
    contacts = db.scalars(scoped(db, Contact, user).options(selectinload(Contact.company))).all()
    for match_type, getter in (("Email", lambda item: normalized(item.email)), ("Phone", lambda item: normalized(item.mobile or item.phone))):
        buckets: dict[str, list[Contact]] = defaultdict(list)
        for item in contacts:
            key = getter(item)
            if key: buckets[key].append(item)
        for key, items in buckets.items():
            if len(items) > 1: groups.append({"entity_type": "contacts", "match_type": match_type, "match_value": key, "records": [{"id": str(item.id), "name": item.name, "detail": f"{item.company.name} · {item.email or item.phone}"} for item in items]})
    return groups


@router.get("/duplicates/")
def duplicates(db: Session = Depends(get_db), user: User = Depends(current_user)):
    groups = duplicate_groups(db, user)
    return {"group_count": len(groups), "record_count": sum(len(group["records"]) for group in groups), "groups": groups}


@router.post("/duplicates/{entity_type}/merge/")
def merge_duplicate(entity_type: str, payload: MergeInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    import_access(user)
    if payload.primary_id == payload.duplicate_id: raise http_error(422, "Choose two different records.")
    if entity_type == "companies":
        primary = db.scalar(scoped(db, Company, user).where(Company.id == payload.primary_id)); duplicate = db.scalar(scoped(db, Company, user).where(Company.id == payload.duplicate_id))
        if not primary or not duplicate: raise http_error(404, "Company not found.")
        db.execute(update(Contact).where(Contact.tenant_id == user.tenant_id, Contact.company_id == duplicate.id).values(company_id=primary.id, updated_by_id=user.id))
        db.execute(update(Pursuit).where(Pursuit.tenant_id == user.tenant_id, Pursuit.company_id == duplicate.id).values(company_id=primary.id, updated_by_id=user.id))
        db.execute(update(Activity).where(Activity.tenant_id == user.tenant_id, Activity.company_id == duplicate.id).values(company_id=primary.id, updated_by_id=user.id))
    elif entity_type == "contacts":
        primary = db.scalar(scoped(db, Contact, user).where(Contact.id == payload.primary_id)); duplicate = db.scalar(scoped(db, Contact, user).where(Contact.id == payload.duplicate_id))
        if not primary or not duplicate: raise http_error(404, "Contact not found.")
        db.execute(update(Activity).where(Activity.tenant_id == user.tenant_id, Activity.contact_id == duplicate.id).values(contact_id=primary.id, updated_by_id=user.id))
        db.execute(update(Opportunity).where(Opportunity.tenant_id == user.tenant_id, Opportunity.primary_contact_id == duplicate.id).values(primary_contact_id=primary.id, updated_by_id=user.id))
        existing = set(db.scalars(select(PursuitContact.pursuit_id).where(PursuitContact.tenant_id == user.tenant_id, PursuitContact.contact_id == primary.id, PursuitContact.is_deleted.is_(False))).all())
        links = db.scalars(scoped(db, PursuitContact, user).where(PursuitContact.contact_id == duplicate.id)).all()
        for link in links:
            if link.pursuit_id in existing: link.is_deleted = True
            else: link.contact_id = primary.id
            link.updated_by_id = user.id
    else:
        raise http_error(404, "Merge type not found.")
    duplicate.is_deleted = True; duplicate.updated_by_id = user.id
    audit(db, user, f"{entity_type[:-1].title()} records merged", detail=f"Kept {primary.id}; archived {duplicate.id}")
    db.commit()
    return {"detail": "Records merged.", "primary_id": str(primary.id), "archived_id": str(duplicate.id)}


@router.get("/quality/")
def data_quality(db: Session = Depends(get_db), user: User = Depends(current_user)):
    issues: list[dict] = []
    companies = db.scalars(scoped(db, Company, user)).all()
    contacts = db.scalars(scoped(db, Contact, user).options(selectinload(Contact.company))).all()
    pursuits = db.scalars(scoped(db, Pursuit, user).options(selectinload(Pursuit.company), selectinload(Pursuit.lead), selectinload(Pursuit.opportunity))).all()
    for item in companies:
        if not item.domain: issues.append({"type": "Company", "id": str(item.id), "name": item.name, "reason": "Missing website domain", "severity": "Medium", "route": "companies"})
        if not item.industry: issues.append({"type": "Company", "id": str(item.id), "name": item.name, "reason": "Missing industry", "severity": "Low", "route": "companies"})
    for item in contacts:
        if not item.email: issues.append({"type": "Contact", "id": str(item.id), "name": item.name, "reason": "Missing email address", "severity": "High", "route": "contacts"})
        if not item.phone and not item.mobile: issues.append({"type": "Contact", "id": str(item.id), "name": item.name, "reason": "Missing phone number", "severity": "Medium", "route": "contacts"})
    today = date.today()
    for item in pursuits:
        closed = item.opportunity and item.opportunity.stage in {"won", "lost"} or item.lead and item.lead.status == "closed"
        if not closed and item.action_date < today: issues.append({"type": "Pursuit", "id": str(item.id), "name": item.name, "reason": "Next action is overdue", "severity": "High", "route": "pipeline" if item.opportunity else "leads"})
        if not closed and not item.next_action.strip(): issues.append({"type": "Pursuit", "id": str(item.id), "name": item.name, "reason": "Missing next action", "severity": "High", "route": "pipeline" if item.opportunity else "leads"})
    duplicates = duplicate_groups(db, user)
    possible_duplicate_records = sum(len(group["records"]) for group in duplicates)
    total = len(companies) + len(contacts) + len(pursuits)
    affected = len({(issue["type"], issue["id"]) for issue in issues}) + possible_duplicate_records
    score = max(0, round(100 * (1 - affected / max(total, 1))))
    return {"score": score, "records_checked": total, "issue_count": len(issues), "duplicate_group_count": len(duplicates), "metrics": {"companies_missing_domain": sum(1 for i in issues if i["reason"] == "Missing website domain"), "contacts_missing_email": sum(1 for i in issues if i["reason"] == "Missing email address"), "contacts_missing_phone": sum(1 for i in issues if i["reason"] == "Missing phone number"), "overdue_actions": sum(1 for i in issues if i["reason"] == "Next action is overdue")}, "issues": issues[:200], "checked_at": datetime.now(timezone.utc)}
