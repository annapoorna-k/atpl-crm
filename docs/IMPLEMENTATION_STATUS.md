# ATPLCRM v0.7 delivery status

This release starts the implementation plan and delivers an executable core. It does not mark all phases complete.

## Delivered in the initial increment

- Independent workspace, Docker topology, generated local secrets, dependency locks and PostgreSQL migration.
- Branded desktop/mobile shell and usable screens for overview, work, attention, companies/contacts, lead board/detail, opportunity board/detail, pre-sales requests, basic reports and configuration inspection.
- Core domain with tenant-scoped reads/writes, separate Lead/Opportunity records sharing persistent pursuit context, conversion, source/team/contact/history preservation, role checks and optimistic work-update conflicts.
- Structured blockers, separate client activity, stages/closure, fixed currency values, financial history, restricted-value presentation and audit events.
- Read/write companies and contacts, lead creation, pre-sales requests, secure artifact links and local notifications.
- Administrator-managed local users, access levels, activation, password resets, reference labels/order/availability, stage probabilities and exchange rates.
- CSV templates, field mapping, dry-run validation, partial imports with error reports and audit/history for companies, contacts and leads.
- Tenant-scoped universal search with type/owner/status/country filters and pagination, duplicate review/merge, and a data-quality score with actionable record issues.
- Automatic one-time CSRF refresh and request recovery when another browser tab rotates the workspace cookie during login or an authenticated action.
- Server-side pagination, filtering and sorting for the four main record lists, plus private saved views for each user.
- Manager bulk owner/Ball-in-Court assignment with audit history and optimistic conflict handling.
- Opportunity stakeholder add, role edit and removal workflows, restricted to same-company contacts and protecting the primary contact.
- Pipeline drag-and-drop with accessible select fallback, evidence capture, locked/version-protected stage transitions and automatic lifecycle timestamps.
- Atomic action completion that preserves immutable history and requires a new owner, action, type and future due date.
- Seven milestone pursuit timeline and aggregate count/median working-day health report.
- Complete server-backed My Work and Needs Attention exception queues, including actions, blockers and pre-sales deliverables.
- User-configurable exception notifications with durable history, PRD recipient/escalation routing, Monday leadership summaries and visible automation health.
- FastAPI workflow tests, TypeScript/production UI build, plus Docker/PostgreSQL and browser verification as recorded in VERIFICATION.md.

## Deliberate limits and remaining work

| Area | Remaining scope |
| Identity | Real Entra OIDC, local OIDC provider replacement for temporary demo password login, provisioned-user lifecycle and stronger login rate limiting. |
| Administration | Fine-grained permission policies and connected-identity provisioning. Local users, global access levels, activation, password resets, reference options, stage probabilities and rates are editable now. |
| Schema | Remaining partner agreement scope/evidence fields, artifact/email/share fields and delivery fields; complete database-level role/tenant constraints and separate runtime/migration privileges. |
| Data entry | Excel imports, background processing beyond the current 5,000-row CSV limit, fuzzy duplicate matching, field-level merge selection, contact engagement updates and remaining opportunity business fields. |
| Pipeline | Remaining specialized filters, configurable working calendars and deeper stage movement analysis. Drag-and-drop, accessible select movement, action completion, stage-edit concurrency and seven-milestone reporting work now. |
| Commercial | Partner-term UI/calculation coverage, rate-update UI/API and refresh, probability snapshot semantics, complete won/lost/handoff fields and approval evidence. Unknown partner formulas currently make net value unavailable rather than inflating it. |
| Activity | Full paginated contact/company histories; current bootstrap returns the latest 50 permitted activities. Future meetings and completed interactions remain separate. |
| Documents | Real upload/storage adapter, Outlook add-in, email linking/attachments, sharing approval/recipients/register, artifact version supersession and reusable library. Basic HTTPS evidence links work. |
| Pre-sales | Full transition matrix, review evidence gate, contributors, per-person weekly capacity and cost analytics. Basic assignee/manager status rules work. |
| Reports | Monthly/quarterly filters, loss/blocker/value-erosion/partner/movement analysis, individual performance, server exports, Excel support and configuration parity. Lifecycle bottlenecks use the current weekday calendar; the lead chart is status distribution, not historical conversion analytics. |
| Search/scale | Search-specific PostgreSQL indexes/full-text ranking, recent-search history, stale-data/query caching and documented 20k/5k/5k performance acceptance. Universal search and the four main record lists paginate on the server. |
| Notifications | Core local phase complete: preferences, recipient/escalation rules, 15-minute scans, Monday summaries, failure alerts, durable in-app history and automation monitoring are implemented. External email/mobile channels may be added only if later required. |
| AI | Entire approved Azure adapter, grounded summaries/extraction, consent/review UI and evaluations. No fake AI buttons. |
| Release quality | Full accessibility contrast/screen-reader audit, visual regression baselines, CI/security scanning, resource limits, image-digest pinning, rotation/retention, restore rehearsal and production deployment. |

## Architectural decisions

1. Standalone ATPLCRM codebase. No imports, runtime calls or shared platform dependencies.
2. FastAPI and SQLAlchemy provide the API and persistence layer; Alembic controls schema changes. PostgreSQL remains the system of record, with Redis/Celery for scheduled reminders. Kafka will be introduced only when a real cross-service event-stream requirement exists.
3. Persistent Pursuit work context with separate one-to-one Lead/Opportunity records preserves linked history during conversion; a converted lead remains closed and traceable.
4. Values and rates use Decimal in the API/database. Frontend numbers are display/basic demo aggregation only; authoritative reports must move to server-side decimal calculation before financial-scale acceptance.
5. Restriction checks apply on the server, including timeline content and the activity feed. SQL triggers protect audit/value history against ordinary UPDATE/DELETE. Separate runtime DB privileges remain pending; an infrastructure administrator can still alter database policy.
6. Phase boundaries are not all complete: foundation, initial identity/schema and core UI slices were built together for a reviewable local product. Do not describe this as production-ready or PRD-complete.

## Next implementation order

1. Entra/OIDC; complete record/field authorization matrix and runtime database privileges.
2. Partners/currencies, complete reports, pre-sales review gates and document/Microsoft integrations.
3. Notifications/operations, AI, hardening and production/connected acceptance.
