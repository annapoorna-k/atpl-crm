"""Central authorization contract for the local and connected ATPLCRM runtimes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .models import User
from .security import current_user
from .services import http_error

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])

ROLE_CAPABILITIES = {
    "Standard": {
        "workspace.view", "relationship.create", "activity.create", "record.edit_assigned",
        "document.register", "report.view", "report.export", "search.use",
    },
    "Manager": {
        "workspace.view", "relationship.create", "activity.create", "record.edit_assigned",
        "document.register", "document.approve_share", "report.view", "report.export",
        "report.view_team", "search.use", "lead.validate", "assignment.bulk", "data.manage",
        "commercial.manage", "presales.manage", "restricted_value.view",
    },
    "Executive": {
        "workspace.view", "relationship.create", "activity.create", "record.edit_assigned",
        "document.register", "document.approve_share", "report.view", "report.export",
        "report.view_team", "search.use", "lead.validate", "assignment.bulk", "data.manage",
        "commercial.manage", "presales.manage", "restricted_value.view",
    },
    "Administrator": {
        "workspace.view", "relationship.create", "activity.create", "record.edit_assigned",
        "document.register", "document.approve_share", "report.view", "report.export",
        "report.view_team", "search.use", "lead.validate", "assignment.bulk", "data.manage",
        "commercial.manage", "presales.manage", "restricted_value.view", "workspace.admin",
        "user.admin", "reference.admin", "automation.admin",
    },
}

CAPABILITY_LABELS = {
    "workspace.view": "View workspace records",
    "relationship.create": "Create companies, contacts and leads",
    "activity.create": "Record client and internal activity",
    "record.edit_assigned": "Edit assigned pursuit work",
    "document.register": "Register documents and emails",
    "document.approve_share": "Approve and share client documents",
    "report.view": "View permission-filtered reports",
    "report.export": "Export permission-filtered reports and lists",
    "report.view_team": "View team performance reports",
    "search.use": "Search visible workspace records",
    "lead.validate": "Independently validate and convert leads",
    "assignment.bulk": "Bulk assign owners and Ball in Court",
    "data.manage": "Import and merge CRM data",
    "commercial.manage": "Manage restricted commercial information",
    "presales.manage": "Assign, review and approve pre-sales work",
    "restricted_value.view": "View restricted values when policy permits",
    "workspace.admin": "Administer workspace configuration",
    "user.admin": "Manage users and access levels",
    "reference.admin": "Manage references, rates and working calendar",
    "automation.admin": "Run and inspect workspace automation",
}

FIELD_RULES = [
    {"area": "Restricted opportunity", "fields": "Value, value history, narrative, activity detail and internal evidence", "rule": "Management or assigned pursuit team"},
    {"area": "Pursuit work", "fields": "Owner, Ball in Court, action, blocker and stage", "rule": "Management or assigned pursuit team"},
    {"area": "Relationship", "fields": "Company and contact profile", "rule": "Relationship owner or management for edits; workspace users may view"},
    {"area": "Administration", "fields": "Users, access, references, rates, calendar and automation", "rule": "Administrator only"},
    {"area": "Reports and exports", "fields": "Aggregates and underlying rows", "rule": "Same field and record permissions as the source data"},
]


def capabilities_for(user: User) -> set[str]:
    return ROLE_CAPABILITIES.get(user.level, ROLE_CAPABILITIES["Standard"])


def has_capability(user: User, capability: str) -> bool:
    return capability in capabilities_for(user)


def require_capability(user: User, capability: str) -> None:
    if not has_capability(user, capability):
        raise http_error(403, f"{CAPABILITY_LABELS.get(capability, capability)} permission is required.")


def permission_contract(user: User) -> dict:
    granted = capabilities_for(user)
    return {
        "role": user.level,
        "capabilities": [
            {"code": code, "label": CAPABILITY_LABELS[code], "granted": code in granted}
            for code in CAPABILITY_LABELS
        ],
        "field_rules": FIELD_RULES,
    }


@router.get("/")
def current_permissions(user: User = Depends(current_user)):
    return permission_contract(user)
