# Requirement traceability — initial implementation

Status meanings: **Implemented** is present in the current local core; **Partial** has additional PRD conditions to deliver; **Planned** is not implemented. Test results are recorded separately in VERIFICATION.md. No row implies production certification.

| PRD IDs | Feature | Status | Primary location |
| FR-01 | Entra single sign-on | Planned | atplcrm/settings.py; temporary local-only session flow in atplcrm/api.py |
| FR-02–05 | Global/pursuit roles, record permissions, restricted values | Partial | editable global access levels and activation plus pursuit roles and restricted values; fine-grained policy editor pending |
| FR-06 | Immutable audit trail | Partial | alembic baseline triggers; comprehensive before/after coverage and runtime privileges pending |
| FR-07 | 12-hour inactivity timeout | Implemented | atplcrm/security.py |
| FR-10–11 | Companies/contacts | Implemented | full company and section 7.5 contact fields, controlled values, ownership/source attribution and responsive create/edit/detail UI |
| FR-12–17 | Activities, histories, sources, do-not-contact | Implemented | fast activity form with backdating, derived client-facing behavior, engagement/first-touch updates, protected outbound overrides and paginated Company/Contact histories |
| FR-18–19 | Import and duplicate resolution | Implemented | mapped CSV/Excel dry runs, full-field row validation, confirmed duplicate warnings, durable history, exact/fuzzy review, field-level merges and reviewed-distinct decisions |
| FR-20 | Contact collision | Implemented | pre-save warning names the owner, last outbound touch and related pursuit; save remains permitted and creates a durable owner notification |
| FR-21 | Universal search | Partial | tenant-scoped server search, type/owner/status/country filters and pagination implemented; ranked full-text indexes and saved recent searches remain |
| FR-25–26 | Lead create/board/list/filters | Implemented | separate lead board plus server-paginated status, owner, holder, source, priority, next-action and last-interaction filters |
| FR-27–29 | Independent validation, preserving conversion, nurture | Implemented | explicit eligible-validator routing, self-validation refusal, history-preserving conversion, nurture revisits and tenant working calendars |
| FR-30 | Bulk assignment | Implemented | productivity.py and RecordList.tsx |
| FR-35–36 | Pipeline and stage changes | Implemented | drag-and-drop cards and accessible selector in App.tsx; evidence, locking, version conflicts and audit history in api.py |
| FR-37–44 | Actions, blockers, engagement, scope, contacts, values, hold and milestones | Implemented | atomic action completion/handoff, immutable histories, editable qualified fields, derived interaction dates, contacts, hold handling, automatic timestamps and seven calendar-aware milestones |
| FR-45–46 | Filters and opportunity page | Implemented | complete opportunity filters plus at-a-glance detail with editable need/scope/contact/service, team, contacts, partners, documents, pre-sales and timeline |
| FR-47 | Probability override | Implemented | override retains comment and stored stage-default snapshot |
| FR-48–50 | Won/lost/approval capture | Implemented | complete loss context/competitor fields and won contract, project, evidence, optional approval and handoff capture |
| FR-51 | Saved views | Implemented | personal saved-view API and RecordList UI |
| FR-55–57 | Deployment currency and fixed stored values | Implemented | US currency enforcement, stored local/USD values and International display toggle |
| FR-58–60 | Rate changes/refresh/bulk re-baseline | Implemented | individual fixed-rate history, admin table override, confirmed selected-open-deal re-baseline, monthly published-source adapter and failure/movement alerts; connected source configuration remains an environment acceptance item |
| FR-65–68 | Partner terms/net value/warnings/report | Implemented | multi-partner UI/API, conditional terms validation, reproducible net calculation, configurable ceiling and undocumented-terms report |
| FR-69 | Partner performance | Implemented | management report for introduced/involved opportunities, win rate and net won value |
| FR-75–80 | Pre-sales queue/request lifecycle/approval/effort | Partial | initial creation/status/assignee/effort; complete approvals and weekly load pending |
| FR-81 | Pre-sales cost | Planned | — |
| FR-85 | Artifact attachments | Partial | secure document links only |
| FR-86–92 | Outlook linking, sharing register, versions, library | Planned | — |
| FR-95–96 | My Work / Needs Attention | Implemented | server-backed action, blocker and deliverable queues plus all specified exception categories in notifications.py and App.tsx |
| FR-97–100 | Pipeline, forecast, lead funnel, drill-down | Partial | overview and basic tables; time filters and historical funnel pending |
| FR-101 | Report/list exports | Partial | visible forecast CSV only; full server/Excel export pending |
| FR-102–107 | Role dashboards and advanced reports | Partial | generic overview and seven-milestone bottleneck report exist; other role and advanced reports pending |
| FR-110–115 | AI assistance | Planned | no provider connected or simulated AI claims |
| Section 13 | Exception notifications and alerts | Implemented | per-user preferences, configurable thresholds, recipient/escalation rules, durable history, 15-minute scans, Monday leadership summaries and automation failure monitoring |
| NFR-01–10 | Hosting/security/backups/performance/residency/mobile/audit/observability/parity | Partial | local Compose, persistent volumes, guards, audit triggers, responsive layout and backup script; full acceptance remains pending |

The original full PRD and the step-by-step implementation plan remain the scope baseline. This matrix tracks the implemented increments and must be updated as each remaining condition is delivered and verified.
