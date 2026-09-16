from __future__ import annotations

import csv
import io
from collections import defaultdict
from copy import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from statistics import median
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .calendar import tenant_calendar, working_days
from .constants import MANAGEMENT, STAGES
from .database import get_db
from .models import AuditEvent, CommercialSetting, Lead, Opportunity, PreSalesRequest, Pursuit, User, ValueHistory
from .presenters import MILESTONES
from .security import current_user
from .services import can_value, commercial_totals, http_error, money, scoped, utc

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
OPEN_STAGES = {"discovery", "qualified", "presales", "proposal", "negotiation", "contract", "hold"}
STAGE_LABELS = dict(STAGES)
RANK = {value: index for index, value in enumerate(["discovery", "qualified", "presales", "proposal", "negotiation", "contract"])}


def period_dates(period: str, from_date: date | None, to_date: date | None) -> tuple[date | None, date]:
    today = date.today()
    if period == "custom":
        if not from_date or not to_date: raise http_error(422, {"period": "Custom reporting requires both dates."})
        if from_date > to_date: raise http_error(422, {"from_date": "The start date must be on or before the end date."})
        return from_date, to_date
    if period == "all": return None, today
    days = {"30d": 30, "90d": 90, "365d": 365, "24m": 730}.get(period)
    if not days: raise http_error(422, {"period": "Choose 30d, 90d, 365d, 24m, all or custom."})
    return today - timedelta(days=days), today


def date_in(value: datetime | date | None, start: date | None, end: date) -> bool:
    if not value: return False
    day = value.date() if isinstance(value, datetime) else value
    return (start is None or day >= start) and day <= end


def options():
    return (
        selectinload(Opportunity.pursuit).selectinload(Pursuit.company),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.owner),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.sourced_by),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.holder),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.blocker_owner),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.lead),
        selectinload(Opportunity.pursuit).selectinload(Pursuit.opportunity),
        selectinload(Opportunity.values),
        selectinload(Opportunity.partners),
    )


def record(opportunity: Opportunity, net: Decimal | None) -> dict:
    pursuit = opportunity.pursuit
    return {
        "id": str(pursuit.id), "opportunity_id": str(opportunity.id), "name": pursuit.name,
        "company": pursuit.company.name, "owner": pursuit.owner.display_name,
        "stage": opportunity.stage, "stage_label": STAGE_LABELS.get(opportunity.stage, opportunity.stage),
        "service_line": opportunity.service_line, "source": pursuit.source_channel,
        "country": pursuit.company.country, "opportunity_type": opportunity.opportunity_type,
        "net_value_usd": str(net) if net is not None else None,
        "probability": opportunity.probability, "expected_close_date": opportunity.expected_close_date,
    }


def opportunity_rows(db: Session, user: User, owner_id: int | None, service_line: str, source: str, country: str, opportunity_type: str):
    rows = list(db.scalars(scoped(db, Opportunity, user).options(*options())).unique().all())
    settings = db.scalar(scoped(db, CommercialSetting, user))
    result = []
    for item in rows:
        pursuit = item.pursuit
        if owner_id and pursuit.owner_id != owner_id: continue
        if service_line and item.service_line != service_line: continue
        if source and pursuit.source_channel != source: continue
        if country and pursuit.company.country != country: continue
        if opportunity_type and item.opportunity_type != opportunity_type: continue
        if not can_value(db, user, item): continue
        result.append((item, commercial_totals(db, item, partners=item.partners, settings=settings)["net_usd"]))
    return result


def group_row(groups: dict, key: str, item: Opportunity, net: Decimal | None, start: date | None, end: date, calendar):
    group = groups.setdefault(key or "Unspecified", {"closed": 0, "won": 0, "won_value": Decimal("0"), "cycle_days": [], "record_ids": []})
    group["closed"] += 1; group["record_ids"].append(str(item.pursuit_id))
    if item.stage == "won":
        group["won"] += 1
        if net is not None: group["won_value"] += net
    if item.pursuit.closed_at:
        group["cycle_days"].append(working_days(item.pursuit.created_at, item.pursuit.closed_at, calendar))


def analytics_data(
    db: Session, user: User, period: str, from_date: date | None, to_date: date | None,
    owner_id: int | None, service_line: str, source: str, country: str, opportunity_type: str, group_by: str,
) -> dict:
    start, end = period_dates(period, from_date, to_date)
    opportunities = opportunity_rows(db, user, owner_id, service_line, source, country, opportunity_type)
    stage_groups = defaultdict(lambda: {"count": 0, "net": Decimal("0"), "ids": []})
    records = []
    for item, net in opportunities:
        records.append(record(item, net))
        if item.stage in OPEN_STAGES:
            row = stage_groups[item.stage]; row["count"] += 1; row["ids"].append(str(item.pursuit_id))
            if net is not None: row["net"] += net
    pipeline = [{"key": key, "label": STAGE_LABELS.get(key, key), "count": stage_groups[key]["count"], "net_value_usd": str(money(stage_groups[key]["net"])), "record_ids": stage_groups[key]["ids"]} for key in STAGE_LABELS if key in stage_groups]

    monthly = defaultdict(lambda: {"net": Decimal("0"), "weighted": Decimal("0"), "ids": []})
    quarterly = defaultdict(lambda: {"net": Decimal("0"), "weighted": Decimal("0"), "ids": []})
    for item, net in opportunities:
        if item.stage not in OPEN_STAGES - {"hold"} or net is None: continue
        close = item.expected_close_date
        month = close.strftime("%Y-%m"); quarter = f"{close.year} Q{(close.month - 1) // 3 + 1}"
        weighted = net * Decimal(item.probability) / 100
        for bucket, key in ((monthly, month), (quarterly, quarter)):
            bucket[key]["net"] += net; bucket[key]["weighted"] += weighted; bucket[key]["ids"].append(str(item.pursuit_id))
    def forecast_rows(values): return [{"period": key, "net_value_usd": str(money(row["net"])), "weighted_value_usd": str(money(row["weighted"])), "count": len(row["ids"]), "record_ids": row["ids"]} for key, row in sorted(values.items())]

    lead_statement = scoped(db, Lead, user).options(selectinload(Lead.pursuit).selectinload(Pursuit.owner), selectinload(Lead.pursuit).selectinload(Pursuit.sourced_by), selectinload(Lead.pursuit).selectinload(Pursuit.company), selectinload(Lead.pursuit).selectinload(Pursuit.lead), selectinload(Lead.pursuit).selectinload(Pursuit.opportunity))
    leads = list(db.scalars(lead_statement).unique().all())
    lead_stages = ["Created", "Worked", "Engaged", "Validated", "Disqualified", "Converted"]
    funnel = {stage: [] for stage in lead_stages}; by_source = defaultdict(lambda: {stage: [] for stage in lead_stages}); by_user = defaultdict(lambda: {stage: [] for stage in lead_stages})
    lead_records = []
    opportunity_record_ids = {row["id"] for row in records}
    for lead in leads:
        p = lead.pursuit
        if not date_in(p.created_at, start, end): continue
        if owner_id and p.owner_id != owner_id or source and p.source_channel != source or country and p.company.country != country: continue
        if str(p.id) not in opportunity_record_ids:
            lead_records.append({"id": str(p.id), "opportunity_id": None, "name": p.name, "company": p.company.name, "owner": p.owner.display_name, "stage": lead.status, "stage_label": lead.outcome or lead.status.replace("_", " ").title(), "service_line": "", "source": p.source_channel, "country": p.company.country, "opportunity_type": "Lead", "net_value_usd": None, "probability": None, "expected_close_date": None})
        stages = ["Created"]
        if lead.status != "new" or p.first_contacted_at: stages.append("Worked")
        if lead.status in {"engaged", "ready", "closed"} or lead.outcome in {"Converted", "Disqualified"}: stages.append("Engaged")
        if p.validated_at or lead.outcome == "Converted": stages.append("Validated")
        if lead.outcome == "Disqualified": stages.append("Disqualified")
        if lead.outcome == "Converted": stages.append("Converted")
        for stage in stages:
            funnel[stage].append(str(p.id)); by_source[p.source_channel][stage].append(str(p.id)); by_user[p.sourced_by.display_name][stage].append(str(p.id))
    funnel_rows = [{"stage": stage, "count": len(funnel[stage]), "record_ids": funnel[stage]} for stage in lead_stages]
    breakdown = lambda values: [{"key": key, **{stage.casefold(): len(ids[stage]) for stage in lead_stages}, "record_ids": sorted(set(sum(ids.values(), [])))} for key, ids in sorted(values.items())]

    reporting_pursuits = {item.pursuit_id: item.pursuit for item, _net in opportunities}
    if not service_line and not opportunity_type:
        reporting_pursuits.update({lead.pursuit_id: lead.pursuit for lead in leads})
    blockers_type = defaultdict(lambda: {"count": 0, "days": [], "ids": []}); blockers_owner = defaultdict(lambda: {"count": 0, "days": [], "ids": []})
    now = datetime.now(timezone.utc)
    for p in reporting_pursuits.values():
        if (p.opportunity and p.opportunity.stage not in OPEN_STAGES) or (not p.opportunity and p.lead.status == "closed") or p.blocker == "None": continue
        days = (now - utc(p.blocked_since or p.updated_at)).days
        for groups, key in ((blockers_type, p.blocker), (blockers_owner, p.blocker_owner.display_name if p.blocker_owner else "Unassigned")):
            row = groups[key]; row["count"] += 1; row["days"].append(days); row["ids"].append(str(p.id))
    blocker_rows = lambda values: [{"key": key, "count": row["count"], "median_days": float(median(row["days"])), "oldest_days": max(row["days"]), "record_ids": row["ids"]} for key, row in sorted(values.items(), key=lambda pair: (-pair[1]["count"], pair[0]))]

    calendar = tenant_calendar(db, user.tenant_id)
    dimension = group_by if group_by in {"service_line", "source", "country", "opportunity_type", "owner"} else "service_line"
    outcome_groups = {}; loss_reasons = defaultdict(lambda: {"count": 0, "ids": []})
    erosion_groups = defaultdict(lambda: {"initial": Decimal("0"), "final": Decimal("0"), "count": 0, "ids": []})
    for item, net in opportunities:
        if item.stage not in {"won", "lost"} or not date_in(item.pursuit.closed_at, start, end): continue
        key = {"service_line": item.service_line, "source": item.pursuit.source_channel, "country": item.pursuit.company.country, "opportunity_type": item.opportunity_type, "owner": item.pursuit.owner.display_name}[dimension]
        group_row(outcome_groups, key, item, net, start, end, calendar)
        if item.stage == "lost":
            loss = loss_reasons[item.loss_reason or "Not recorded"]; loss["count"] += 1; loss["ids"].append(str(item.pursuit_id))
        if item.stage == "won":
            initial = next((value for value in sorted(item.values, key=lambda value: value.created_at) if value.value_type == "Initial estimate"), None)
            final = next((value for value in sorted(item.values, key=lambda value: value.created_at, reverse=True) if value.value_type == "Final contract value"), None)
            if initial and final:
                erosion_key = item.service_line if dimension != "owner" else item.pursuit.owner.display_name
                row = erosion_groups[erosion_key]; row["initial"] += initial.amount * initial.fx_rate; row["final"] += final.amount * final.fx_rate; row["count"] += 1; row["ids"].append(str(item.pursuit_id))
    outcomes = []
    for key, row in sorted(outcome_groups.items()):
        outcomes.append({"key": key, "closed": row["closed"], "won": row["won"], "win_rate_pct": str((Decimal(row["won"]) / row["closed"] * 100).quantize(Decimal("0.01"))), "average_deal_size_usd": str(money(row["won_value"] / row["won"])) if row["won"] else None, "median_cycle_working_days": float(median(row["cycle_days"])) if row["cycle_days"] else None, "record_ids": row["record_ids"]})
    erosion = [{"key": key, "deal_count": row["count"], "initial_usd": str(money(row["initial"])), "final_usd": str(money(row["final"])), "erosion_usd": str(money(row["initial"] - row["final"])), "erosion_pct": str(((row["initial"] - row["final"]) / row["initial"] * 100).quantize(Decimal("0.01"))) if row["initial"] else "0.00", "record_ids": row["ids"]} for key, row in sorted(erosion_groups.items())]

    visible_pursuit_ids = set(reporting_pursuits)
    event_rows = db.execute(select(AuditEvent, Pursuit).join(Pursuit, Pursuit.id == AuditEvent.pursuit_id).where(AuditEvent.tenant_id == user.tenant_id, AuditEvent.pursuit_id.in_(visible_pursuit_ids), AuditEvent.is_deleted.is_(False), AuditEvent.created_at >= datetime.combine(start or date(1970,1,1), datetime.min.time(), tzinfo=timezone.utc), AuditEvent.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))).all() if visible_pursuit_ids else []
    movement = {key: set() for key in ("entered", "advanced", "regressed", "closed", "slipped")}
    for event, pursuit in event_rows:
        before, after = event.before or {}, event.after or {}
        if event.action == "Stage changed":
            old, new = str(before.get("stage", "")), str(after.get("stage", ""))
            if new in {"won", "lost"}: movement["closed"].add(str(pursuit.id))
            elif old in RANK and new in RANK:
                movement["advanced" if RANK[new] > RANK[old] else "regressed"].add(str(pursuit.id))
        if event.action == "Opportunity details updated" and before.get("close") and after.get("close") and str(after["close"]) > str(before["close"]): movement["slipped"].add(str(pursuit.id))
    for item, _net in opportunities:
        if date_in(item.pursuit.validated_at, start, end): movement["entered"].add(str(item.pursuit_id))
    movement_rows = [{"key": key, "count": len(ids), "record_ids": sorted(ids)} for key, ids in movement.items()]

    users = list(db.scalars(select(User).where(User.tenant_id == user.tenant_id, User.is_active.is_(True)).order_by(User.first_name, User.last_name)).all())
    delivered = list(db.scalars(scoped(db, PreSalesRequest, user).where(PreSalesRequest.status == "Delivered").options(selectinload(PreSalesRequest.opportunity))).all())
    performance = []
    for person in users:
        if user.level not in MANAGEMENT and person.id != user.id: continue
        generated = [str(lead.pursuit_id) for lead in leads if lead.pursuit.sourced_by_id == person.id and date_in(lead.pursuit.created_at, start, end)]
        owned = [str(item.pursuit_id) for item, _net in opportunities if item.pursuit.owner_id == person.id and item.stage in OPEN_STAGES]
        delivered_ids = [str(row.opportunity.pursuit_id) for row in delivered if row.assigned_to_id == person.id and date_in(row.delivered_at, start, end)]
        ball = [str(p.id) for p in reporting_pursuits.values() if p.holder_id == person.id and ((p.opportunity and p.opportunity.stage in OPEN_STAGES) or (not p.opportunity and p.lead.status != "closed"))]
        blocked = [str(p.id) for p in reporting_pursuits.values() if p.blocker_owner_id == person.id and p.blocker != "None" and ((p.opportunity and p.opportunity.stage in OPEN_STAGES) or (not p.opportunity and p.lead.status != "closed"))]
        performance.append({"user_id": person.id, "user": person.display_name, "leads_generated": len(generated), "leads_generated_ids": generated, "opportunities_owned": len(owned), "opportunities_owned_ids": owned, "presales_delivered": len(delivered_ids), "presales_delivered_ids": delivered_ids, "ball_in_court": len(ball), "ball_in_court_ids": ball, "blockers_owned": len(blocked), "blockers_owned_ids": blocked})

    milestones = []
    pursuits = list(reporting_pursuits.values())
    for index, (key, label, attribute) in enumerate(MILESTONES):
        elapsed, ids = [], []
        for pursuit in pursuits:
            complete = getattr(pursuit, attribute)
            if not complete: continue
            ids.append(str(pursuit.id))
            if index:
                previous = getattr(pursuit, MILESTONES[index - 1][2])
                if previous: elapsed.append(working_days(previous, complete, calendar))
        milestones.append({"key": key, "label": label, "count": len(ids), "median_working_days": float(median(elapsed)) if elapsed else (0 if not index and ids else None), "record_ids": ids})

    return {
        "filters": {"period": period, "from_date": start, "to_date": end, "owner_id": owner_id, "service_line": service_line, "source": source, "country": country, "opportunity_type": opportunity_type, "group_by": dimension},
        "pipeline": pipeline, "pipeline_total_usd": str(money(sum((Decimal(row["net_value_usd"]) for row in pipeline), Decimal("0")))),
        "forecast_month": forecast_rows(monthly), "forecast_quarter": forecast_rows(quarterly),
        "lead_funnel": funnel_rows, "lead_by_source": breakdown(by_source), "lead_by_user": breakdown(by_user),
        "blockers_by_type": blocker_rows(blockers_type), "blockers_by_owner": blocker_rows(blockers_owner),
        "outcomes": outcomes, "loss_reasons": [{"key": key, **row} for key, row in sorted(loss_reasons.items())],
        "value_erosion": erosion, "movement": movement_rows, "performance": performance,
        "milestones": milestones, "records": records + lead_records,
    }


@router.get("/analytics/")
def analytics(
    period: str = "365d", from_date: date | None = None, to_date: date | None = None,
    owner_id: int | None = None, service_line: str = "", source: str = "", country: str = "",
    opportunity_type: str = "", group_by: str = "service_line",
    db: Session = Depends(get_db), user: User = Depends(current_user),
):
    return analytics_data(db, user, period, from_date, to_date, owner_id, service_line, source, country, opportunity_type, group_by)


@router.get("/home/")
def role_home(db: Session = Depends(get_db), user: User = Depends(current_user)):
    data = analytics_data(db, user, "365d", None, None, None, "", "", "", "", "service_line")
    all_records = data["records"]; open_ids = [row["id"] for row in all_records if row["stage"] in OPEN_STAGES]
    title = (user.job_title or "").casefold()
    if "pre-sales" in title or "presales" in title:
        own = next((row for row in data["performance"] if row["user_id"] == user.id), None) or {}
        requests = list(db.scalars(scoped(db, PreSalesRequest, user).where(PreSalesRequest.status.notin_(["Delivered", "Cancelled"]))).all())
        request_ids = [str(row.opportunity.pursuit_id) for row in requests]
        cards = [("Open pre-sales queue", len(requests), "presales", request_ids), ("Delivered this year", own.get("presales_delivered", 0), "presales", own.get("presales_delivered_ids", [])), ("Blockers owned", own.get("blockers_owned", 0), "attention", own.get("blockers_owned_ids", [])), ("Current handoffs", own.get("ball_in_court", 0), "work", own.get("ball_in_court_ids", []))]
        role = "Head of Pre-Sales"
    elif user.level in {"Executive", "Administrator"}:
        won = sum(row["won"] for row in data["outcomes"]); closed = sum(row["closed"] for row in data["outcomes"])
        cards = [("Net open pipeline", data["pipeline_total_usd"], "reports", open_ids), ("Weighted forecast", str(money(sum((Decimal(row["weighted_value_usd"]) for row in data["forecast_month"]), Decimal("0")))), "reports", sum((row["record_ids"] for row in data["forecast_month"]), [])), ("Win rate", f"{(Decimal(won) / closed * 100).quantize(Decimal('0.1')) if closed else 0}%", "reports", sum((row["record_ids"] for row in data["outcomes"]), [])), ("Open blockers", sum(row["count"] for row in data["blockers_by_type"]), "attention", sum((row["record_ids"] for row in data["blockers_by_type"]), []))]
        role = "Executive"
    elif "sales" in title or user.level == "Manager":
        ready = sum(row["count"] for row in data["lead_funnel"] if row["stage"] == "Validated")
        cards = [("Net open pipeline", data["pipeline_total_usd"], "pipeline", open_ids), ("Validated leads", ready, "leads", next((row["record_ids"] for row in data["lead_funnel"] if row["stage"] == "Validated"), [])), ("Open blockers", sum(row["count"] for row in data["blockers_by_type"]), "attention", sum((row["record_ids"] for row in data["blockers_by_type"]), [])), ("Forecast periods", len(data["forecast_month"]), "reports", sum((row["record_ids"] for row in data["forecast_month"]), []))]
        role = "Head of Sales"
    else:
        own = next((row for row in data["performance"] if row["user_id"] == user.id), None) or {}
        cards = [("Opportunities owned", own.get("opportunities_owned", 0), "pipeline", own.get("opportunities_owned_ids", [])), ("Ball in court", own.get("ball_in_court", 0), "work", own.get("ball_in_court_ids", [])), ("Blockers owned", own.get("blockers_owned", 0), "attention", own.get("blockers_owned_ids", [])), ("Leads generated", own.get("leads_generated", 0), "leads", own.get("leads_generated_ids", []))]
        role = "Individual contributor"
    return {
        "role": role,
        "cards": [
            {"label": label, "value": str(value), "route": route, "record_ids": ids}
            for label, value, route, ids in cards
        ],
        "visuals": {
            "pipeline": data["pipeline"],
            "forecast_month": data["forecast_month"][:6],
            "lead_funnel": data["lead_funnel"],
        },
    }


def export_rows(data: dict, report: str):
    mapping = {
        "pipeline": data["pipeline"], "forecast_month": data["forecast_month"], "forecast_quarter": data["forecast_quarter"],
        "lead_funnel": data["lead_funnel"], "lead_by_source": data["lead_by_source"], "lead_by_user": data["lead_by_user"],
        "blockers_by_type": data["blockers_by_type"], "blockers_by_owner": data["blockers_by_owner"],
        "outcomes": data["outcomes"], "loss_reasons": data["loss_reasons"], "value_erosion": data["value_erosion"],
        "movement": data["movement"], "performance": data["performance"], "milestones": data["milestones"], "records": data["records"],
    }
    if report not in mapping: raise http_error(422, {"report": "Choose a supported report."})
    rows = mapping[report]
    return [{key: ", ".join(value) if isinstance(value, list) else value for key, value in row.items()} for row in rows]


@router.get("/export/")
def export_report(
    report: str, format: str = "csv", period: str = "365d", from_date: date | None = None, to_date: date | None = None,
    owner_id: int | None = None, service_line: str = "", source: str = "", country: str = "", opportunity_type: str = "", group_by: str = "service_line",
    db: Session = Depends(get_db), user: User = Depends(current_user),
):
    if format not in {"csv", "xlsx"}: raise http_error(422, {"format": "Choose csv or xlsx."})
    data = analytics_data(db, user, period, from_date, to_date, owner_id, service_line, source, country, opportunity_type, group_by)
    rows = export_rows(data, report); headers = list(rows[0]) if rows else ["No matching records"]
    if format == "csv":
        stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=headers); writer.writeheader()
        for row in rows:
            safe = {key: f"'{value}" if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for key, value in row.items()}; writer.writerow(safe)
        payload = stream.getvalue().encode("utf-8-sig"); media = "text/csv; charset=utf-8"
    else:
        book = Workbook(); sheet = book.active; sheet.title = report[:31]; sheet.append(headers)
        for row in rows: sheet.append([row.get(header) for header in headers])
        for cell in sheet[1]:
            font = copy(cell.font); font.bold = True; cell.font = font
        output = io.BytesIO(); book.save(output); payload = output.getvalue(); media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(io.BytesIO(payload), media_type=media, headers={"Content-Disposition": f'attachment; filename="ATPLCRM-{report}-{date.today()}.{format}"'})
