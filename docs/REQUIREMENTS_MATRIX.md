# Requirement traceability — initial implementation

Status meanings: **Implemented** is present in the current local core; **Partial** has additional PRD conditions to deliver; **Planned** is not implemented. Test results are recorded separately in VERIFICATION.md. No row implies production certification.

| PRD IDs | Feature | Status | Primary location |
| FR-01 | Entra single sign-on | Planned | atplcrm/settings.py; temporary local-only session flow in atplcrm/api.py |
| FR-02–05 | Global/pursuit roles, record permissions, restricted values | Partial | editable global access levels and activation plus pursuit roles and restricted values; fine-grained policy editor pending |
| FR-06 | Immutable audit trail | Partial | alembic baseline triggers; comprehensive before/after coverage and runtime privileges pending |
| FR-07 | 12-hour inactivity timeout | Implemented | atplcrm/security.py |
| FR-10–11 | Companies/contacts | Partial | atplcrm/schemas.py and api.py; full field editing pending |
| FR-12–17 | Activities, histories, sources, do-not-contact | Partial | atplcrm/api.py; paginated complete histories and speed acceptance pending |
| FR-18–19 | Import and duplicate resolution | Partial | mapped CSV dry-run/import/error history and exact duplicate merge are implemented; Excel, fuzzy rules and field-level merge choice remain |
| FR-20 | Contact collision | Partial | warning/notification exists; prior-touch contextual prompt pending |
| FR-21 | Universal search | Partial | tenant-scoped server search, type/owner/status/country filters and pagination implemented; ranked full-text indexes and saved recent searches remain |
| FR-25–26 | Lead create/board/list/filters | Partial | web/src/App.tsx; full filter set pending |
| FR-27–29 | Independent validation, preserving conversion, nurture | Partial | atplcrm/services.py and api.py; explicit alternate routing and configurable calendars pending |
| FR-30 | Bulk assignment | Planned | — |
| FR-35–36 | Pipeline and stage changes | Partial | cards and accessible stage selector; drag-and-drop pending |
| FR-37–44 | Actions, blockers, engagement, scope, contacts, values, hold and milestones | Partial | atplcrm/models.py, services.py and api.py; full stakeholder editor and lifecycle metrics pending |
| FR-45–46 | Filters and opportunity page | Partial | core page exists; all filters and completed partner/document modules pending |
| FR-47 | Probability override | Implemented | FastAPI opportunity action route and detail UI |
| FR-48–50 | Won/lost/approval capture | Partial | stage evidence validation exists; complete capture and approval-recorded editor pending |
| FR-51 | Saved views | Planned | — |
| FR-55–57 | Deployment currency and fixed stored values | Partial | US currency enforcement and stored amounts; local/USD display toggle pending |
| FR-58–60 | Rate changes/refresh/bulk re-baseline | Planned | — |
| FR-65–68 | Partner terms/net value/warnings/report | Partial | base model and supported deduction calculation only |
| FR-69 | Partner performance | Planned | — |
| FR-75–80 | Pre-sales queue/request lifecycle/approval/effort | Partial | initial creation/status/assignee/effort; complete approvals and weekly load pending |
| FR-81 | Pre-sales cost | Planned | — |
| FR-85 | Artifact attachments | Partial | secure document links only |
| FR-86–92 | Outlook linking, sharing register, versions, library | Planned | — |
| FR-95–96 | My Work / Needs Attention | Partial | core action/blocker screens; all requested exception types pending |
| FR-97–100 | Pipeline, forecast, lead funnel, drill-down | Partial | overview and basic tables; time filters and historical funnel pending |
| FR-101 | Report/list exports | Partial | visible forecast CSV only; full server/Excel export pending |
| FR-102–107 | Role dashboards and advanced reports | Planned | generic overview exists |
| FR-110–115 | AI assistance | Planned | no provider connected or simulated AI claims |
| NFR-01–10 | Hosting/security/backups/performance/residency/mobile/audit/observability/parity | Partial | local Compose, persistent volumes, guards, audit triggers, responsive layout and backup script; full acceptance remains pending |

The original full PRD and the step-by-step implementation plan remain the scope baseline. This matrix tracks the first increment only and must be updated as each remaining condition is implemented and verified.
