# ATPLCRM v0.14 delivery status

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
- Seven milestone pursuit timeline, configurable tenant working calendar and aggregate count/median working-day health report.
- Complete lead/opportunity filters, explicit alternate-validator routing, editable qualified opportunity fields and management stage-movement analysis.
- Complete pre-sales lifecycle with request concurrency, Head assignment, tech-lead acceptance, contributors, evidence-backed review/approval/share gate, actual effort, weekly capacity and actual-day cost reporting.
- Complete server-backed My Work and Needs Attention exception queues, including actions, blockers and pre-sales deliverables.
- User-configurable exception notifications with durable history, PRD recipient/escalation routing, Monday leadership summaries and visible automation health.
- Complete commercial workspace: multiple partner involvements, validated contract/margin/fixed/commission/spread terms, evidence status, configurable 40% share warning, reproducible net values, partner reports, fixed-rate updates, confirmed bulk re-baselining and monthly published-rate adapter with movement/failure alerts.
- Opportunity close capture now retains loss context/competitor data or won contract, project-start, duration, final evidence, optional approval evidence and delivery handoff notes. Probability overrides retain the stage-default snapshot.
- Company/contact/activity completion: every section 7.5 contact field is editable, source attribution and controlled engagement are enforced, first/last/touch metrics are derived, do-not-contact overrides are retained, collision warnings include prior outreach context, and Company 360/Contact Detail use full paginated histories.
- Import/data-quality completion: CSV and `.xlsx` dry runs support mapped full-field company/contact/lead imports up to 20,000 rows, within-file and existing-record validation, confirmed fuzzy warnings, durable job results, field-by-field duplicate merges/dismissals and actionable filtered quality reporting.
- Documents/email completion: private managed uploads, Microsoft 365 links, selected-email metadata and automatic attachment registration, classification, manager approval, named-recipient sharing, company/opportunity registers, version supersession and a reusable searchable asset library.
- Reporting completion: role-specific home views plus server-calculated pipeline, monthly/quarterly forecast, historical lead funnel, seven-transition bottlenecks, blocker ageing, win/loss, loss reason, value erosion, movement and individual performance reports. Figures drill into governed records and all report datasets export to CSV or Excel.
- FastAPI workflow tests, TypeScript/production UI build, plus Docker/PostgreSQL and browser verification as recorded in VERIFICATION.md.

## Deliberate limits and remaining work

| Area | Remaining scope |
| Identity | Real Entra OIDC, local OIDC provider replacement for temporary demo password login, provisioned-user lifecycle and stronger login rate limiting. |
| Administration | Fine-grained permission policies and connected-identity provisioning. Local users, global access levels, activation, password resets, reference options, stage probabilities and rates are editable now. |
| Schema | Complete database-level role/tenant constraints and separate runtime/migration privileges. Artifact/email/share, commercial partner, closure and rate-governance fields are complete. |
| Data entry | Company/contact/lead CSV and Excel import plus duplicate/data-quality workflows and qualified opportunity editing are complete locally. Connected-volume performance acceptance remains pending. |
| Pipeline | Lead and opportunity workflow is complete locally: specialized filters, alternate validation routing, editable qualified fields, configurable working calendars, stage movement analysis, drag-and-drop, action completion, concurrency protection and seven milestones. Connected-scale acceptance remains pending. |
| Commercial | Local implementation complete. Configure and approve `FX_RATES_URL`/source before connected monthly refresh acceptance; synthetic rates remain clearly labelled. |
| Activity | Company/contact completion is implemented with paginated protected histories, collision context, engagement updates and retained overrides. Scale acceptance at the PRD target remains pending. |
| Documents | Local workflows are complete with a private Docker volume and an Outlook task-pane package. Azure Blob/SharePoint/Graph adapters, add-in tenant deployment and connected acceptance require the Azure environment and Entra application configuration. |
| Pre-sales | Local implementation complete: Head of Pre-Sales assignment, tech-lead acceptance, nine-state transition matrix, contributors, deliverable/review/share gates, actual effort, weekly capacity and cost analytics. Connected-scale acceptance remains pending. |
| Reports | Local feature scope complete: date/owner/service/source/country/opportunity-type filters, current pipeline, monthly/quarterly weighted forecast, historical funnel, bottlenecks, blockers, outcomes, loss reasons, erosion, movement, individual performance, role home cards, governed drill-down and CSV/Excel exports. Connected-scale reconciliation remains pending. |
| Search/scale | Search-specific PostgreSQL indexes/full-text ranking, recent-search history, stale-data/query caching and documented 20k/5k/5k performance acceptance. Universal search and the four main record lists paginate on the server. |
| Notifications | Core local phase complete: preferences, recipient/escalation rules, 15-minute scans, Monday summaries, failure alerts, durable in-app history and automation monitoring are implemented. External email/mobile channels may be added only if later required. |
| AI | Entire approved Azure adapter, grounded summaries/extraction, consent/review UI and evaluations. No fake AI buttons. |
| Release quality | Full accessibility contrast/screen-reader audit, visual regression baselines, CI/security scanning, resource limits, image-digest pinning, rotation/retention, restore rehearsal and production deployment. |

## Architectural decisions

1. Standalone ATPLCRM codebase. No imports, runtime calls or shared platform dependencies.
2. FastAPI and SQLAlchemy provide the API and persistence layer; Alembic controls schema changes. PostgreSQL remains the system of record, with Redis/Celery for scheduled reminders. Kafka will be introduced only when a real cross-service event-stream requirement exists.
3. Persistent Pursuit work context with separate one-to-one Lead/Opportunity records preserves linked history during conversion; a converted lead remains closed and traceable.
4. Values and rates use Decimal in the API/database. The v0.14 management reports calculate authoritative net and weighted values on the server; connected-scale financial reconciliation remains an acceptance gate.
5. Restriction checks apply on the server, including timeline content and the activity feed. SQL triggers protect audit/value history against ordinary UPDATE/DELETE. Separate runtime DB privileges remain pending; an infrastructure administrator can still alter database policy.
6. Phase boundaries are not all complete: foundation, initial identity/schema and core UI slices were built together for a reviewable local product. Do not describe this as production-ready or PRD-complete.

## Next implementation order

1. Entra/OIDC; complete record/field authorization matrix and runtime database privileges.
2. Activate the Azure Microsoft adapters and complete search/scale work.
3. AI, hardening and production/connected acceptance.
