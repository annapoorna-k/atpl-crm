# ATPLCRM Implementation Plan
## Scope and delivery approach
Build the complete internal CRM described in Soothsayer CRM Requirements v4.0 under the product name ATPLCRM. Brand: dark blue, yellow, grey and white. Deliver the UI, API, database, background jobs, Microsoft integrations, reporting, AI assistance and repeatable local Docker deployment.
This is an implementation plan, not an implementation completion report. Commands, paths and services below are proposed deliverables. Local acceptance and real Microsoft integration acceptance are separate gates. Product commercialization remains a later explicit decision.
Use an entirely independent repository at /Users/n22/Desktop/ATPLCRM. This tool has no relation to Orbit or any other platform. Keep independent dependencies, resource names, credentials and version history. Establish a requirement-to-feature-to-test matrix covering all FR, NFR and acceptance criteria before coding.
Deliver vertical slices: database, business rules, API, UI and tests together. Docker starts in the foundation phase and evolves throughout the build. Do not defer all UI or all testing to the end.

## 1. Architecture and technology
| Layer | Proposed choice and reason |
| Web UI | React + TypeScript + Vite; application routing, TanStack Query/Table, React Hook Form and schema validation. Good fit for a private application without public SEO requirements. |
| Design system | Tailwind CSS with accessible Radix-based components, shared brand tokens, Storybook, and a consistent icon set. Components still require accessibility testing. |
| API | FastAPI + Pydantic + SQLAlchemy, organized as a modular monolith. Strong typed contracts and relational transactions with less deployment overhead than microservices. |
| Contracts | Versioned /api/v1 endpoints, OpenAPI schema, generated TypeScript client and consistent validation/error formats. |
| Data | PostgreSQL; decimal money values, foreign keys, constraints, indexed tenant-scoped queries and transactional business operations. |
| Jobs | Celery worker and one scheduler, with Redis for queue/cache. Jobs are idempotent and use bounded retries. |
| Identity | Entra ID OIDC for connected deployment; local-only OIDC provider for synthetic-data development. Browser uses secure server-managed sessions; no access tokens in localStorage. |
| Documents | Microsoft Graph/SharePoint/OneDrive in connected mode; filesystem adapter with persistent Docker volume in local-demo mode. |
| AI | Internal AI service with approved Azure OpenAI adapter; deterministic fixture adapter for local tests. |
| Deployment | Docker Compose, reverse proxy, multi-stage images, health checks, named volumes and explicit migration/init jobs. |
| Quality | Backend tests, frontend component tests, Playwright end-to-end tests, accessibility checks, security scanning and load tests. |
Pin supported stable dependency versions and image digests during foundation work, commit lockfiles and define an upgrade policy. Use supported FastAPI, SQLAlchemy and Alembic releases. Avoid unnecessary Kubernetes, Elasticsearch and distributed services at this scale.

## 2. Target folder structure
> atplcrm/ — independent repository
> apps/web/ — src/app, routes, features, components, layouts, styles, api, test
> apps/api/ — FastAPI package, domain models, integrations, Alembic migrations and tests
> apps/api/apps/ — identity, tenancy, reference_data, accounts, contacts, pursuits, leads, opportunities, activities, blockers, valuations, partners, presales, artifacts, notifications, reporting, imports, audit, ai
> apps/outlook-addin/ — manifest, taskpane, authentication and linking flow
> packages/ — design-tokens, generated-api-client
> infra/docker/ — web, api, proxy, local-identity and entrypoint configuration
> infra/compose/ — base, development, local-demo and connected configuration
> scripts/ — bootstrap, migrate, seed, smoke-test, backup, restore and verify
> tests/ — e2e, integration, accessibility, performance and security
> docs/ — requirements, architecture/ADRs, permissions, design, API, runbooks and acceptance evidence
> .github/workflows/ — lint, test, build, scan and release
> .env.example, .gitignore, compose.yaml, Makefile, README.md
Frontend feature folders mirror user-facing domains. Business rules live in backend domain services; controllers and UI components do not independently implement conversion, forecast or authorization rules. Background workers call the same domain services.

## 3. Visual direction and experience standards
| Token | Colour | Use |
| Brand navy | #102A43 | Sidebar, major headings and strong actions |
| Deep navy | #0B1F33 | Header and high-emphasis surfaces |
| Brand yellow | #F4C542 | Selected accents and primary highlighted action; use dark text |
| Page grey | #F3F5F7 | Workspace background |
| Border grey | #D9E1E8 | Dividers and form boundaries |
| Text grey | #526170 | Secondary text, subject to contrast checks |
| White | #FFFFFF | Cards, tables, dialogs and content areas |
Use semantic red, green and amber only where status needs them; always pair colour with text/icons. Yellow is an accent, not a large reading surface. Validate actual colour pairings against WCAG 2.2 AA rather than assuming brand tokens are accessible.
Layout: dark sidebar, compact top bar with search/instance indicator/profile, page title and actions, filter row, then content. Distinguish the US and International instance visibly on every page. Default landing is My Work, with user-saved alternatives.
Design all states: loading skeletons, first-use empty states, no search results, validation errors, permission denial, expired sessions, retryable failures, successful saves and unsaved changes. Use clear language, consistent spacing, visible focus, keyboard navigation, accessible dialogs and screen-reader labels.
Pipeline cards show company, deal, value/currency, owner, Ball in Court, close date, next-action date and warning. Provide an explicit Move stage action for keyboard and touch users alongside drag-and-drop. Keep undo/recovery only where the underlying business action safely supports it.
Opportunity header shows stage, commercial owner, holder, next action/type/date, blocker/owner/days, client interaction, next meeting, value/USD equivalent and probability without scrolling on desktop. On mobile prioritize these in a readable stacked summary.
Responsive layouts target desktop, tablet and phone. Use locale-aware dates/numbers/currencies, UTC timestamps with user-timezone display, date-only types for date-only business fields, and configurable working-day calendars. Prepare translation-friendly strings; English is the initial language. Additional translations and RTL localization are future scope unless explicitly requested.
Accessibility target: WCAG 2.2 AA. Security verification target: applicable OWASP ASVS Level 2 controls, with evidence rather than a certification claim.

## Phase 0 — Requirement baseline and design decisions
Estimated effort: 3–4 working days. Dependency: none.
1. Create the independent project folder and repository, README, decision log, issue templates and requirements matrix.
2. Map every requirement to delivery phase, API/domain, screen and acceptance test. Keep the original exclusion list.
3. Define the complete permissions matrix, including conversion, restriction, exports, search, AI context, artifacts and administration.
4. Resolve contradictory requirements through documented proposed defaults: include basic artifact evidence and net-value foundations before live forecasting; define blockers on leads and opportunities; deliver revisit jobs with the first nurture feature; include bulk assignment early.
5. Define partner calculation rules for fixed fees, contract percentages, margin percentages and unknown terms. Do not silently forecast unsupported arrangements as zero deduction. Gross-margin terms need a defined margin input; warn/mark forecasts provisional where terms are unresolved.
6. Define currency edits after value history exists, blocker replacement/history semantics, timezone/date validation, reactivation after nurture and whether direct opportunity creation is permitted. Default to validated conversion only unless approved otherwise.
7. Draw low-fidelity designs for all 12 screens, with stakeholder review of My Work, Lead Board and Opportunity Detail first.
8. Identify required Entra/Graph/SharePoint/Azure AI access and decide the local-demo versus connected acceptance environments.
Exit: requirements are traceable, major data/permission ambiguities have proposed decisions and the first UI flows are ready to build. Routine design choices do not require reopening scope.

## Phase 1 — Foundation, Docker and brand system
Estimated effort: 4–5 working days. Dependency: Phase 0.
1. Scaffold web/API folders, formatting, linting, type checking, environment validation and lockfiles.
2. Establish CI for lint, tests, OpenAPI drift, migrations, image builds and dependency/secret scans.
3. Add PostgreSQL, Redis, API, worker, scheduler and proxy to Docker Compose. Bind public local ports to loopback; keep database/queue ports private by default.
4. Add health/readiness endpoints, dependency health checks, persistent volumes and one-shot migration/init services. API/worker startup must wait for successful initialization; never race migrations across workers.
5. Build the branded app shell, typography, buttons, inputs, tables, status chips, drawers, dialogs, notifications, skeletons and charts in Storybook.
6. Configure generated API client, shared error handling, session handling and logging with correlation IDs and sensitive-data redaction.
7. Create deterministic synthetic seed fixtures and a first smoke test that loads the shell through Docker.
Exit: a fresh checkout boots through the documented command; the branded shell and API are reachable and database state survives restarts.

## Phase 2 — Identity, schema, permissions and audit
Estimated effort: 5–7 working days. Dependency: Phase 1.
1. Implement Entra sign-in, account mapping, global roles, logout and 12-hour inactivity expiration. Provide a local-only OIDC provider with seeded demo identities; no production authentication bypass.
2. Create the full schema, including later objects: company, contact, lead, opportunity, pursuit-contact/team, value history, partner, activity, pre-sales request, artifact, user and exchange rates. Add support tables for tenant, sessions, stage/handoff history, blockers, jobs, import batches and notifications.
3. Model shared pursuit behaviour without duplicating companies/contacts. Enforce valid lead-or-opportunity relationships, single required roles and unique contact email within a deployment.
4. Apply tenant scoping to every query and background job; add database constraints and cross-tenant tests. Keep US/International databases, accounts, queues and storage independent.
5. Implement record authorization and Restricted-field filtering on API reads/writes, exports, reports, search indexes, file access and AI context. Do not hide values only in the browser.
6. Implement immutable audit records and append-only value/event history. Use separate database privileges so the runtime role cannot rewrite audit history; migrations use a separate privileged role.
7. Add soft deletion, optimistic concurrency/version checks and atomic transactions for critical actions.
8. Build administration screens for users, permissions, reference lists, stages, probabilities and deployment settings.
Exit: automated permission tests cover every role and sensitive path, including self-validation refusal, cross-tenant access and restricted-value leakage.

## Phase 3 — Companies, contacts and outreach UI
Estimated effort: 4–6 working days. Dependency: Phase 2.
1. Build company/contact create, read and edit flows with all specified fields and inline company creation.
2. Build Company 360 and Contact Detail with linked pursuits and activity timelines.
3. Implement fast activity entry for every channel/outcome, client-facing classification, first touch, touch count and last interaction calculations. Handle backdated activities correctly.
4. Enforce Do not contact override reasons, source attribution and consent basis.
5. Build CSV/Excel import wizard: upload, map columns, dry run, validation preview, duplicate resolution and result/error download. Large imports run as jobs; retries must not duplicate records.
6. Add duplicate/collision warnings and owner notifications; avoid automatic fuzzy merges. Add global-account fields and primary region.
7. Test spreadsheet formula injection protections on exports and strict upload size/type limits.
Exit: a user imports 200 event contacts/leads, resolves duplicates and logs outreach quickly using desktop and mobile layouts.

## Phase 4 — Leads, validation and conversion
Estimated effort: 4–6 working days. Dependency: Phase 3.
1. Build the five-status board, filtered list and Lead Detail, with ownership, source, contacts and outreach.
2. Add next action/type/date, Ball in Court history, blockers, bulk assignment and a validation queue.
3. Implement independent validation, rejection reasons, alternate routing, nurture/revisit dates and working-day ageing.
4. Convert atomically and idempotently: preserve contacts, activities, artifacts, source attribution and timestamps; create permanent two-way links; never duplicate the opportunity on retry.
5. Gather required opportunity data during conversion, with a usable draft form before committing.
6. Prevent pre-sales requests on unvalidated leads. Keep all unconverted leads out of forecasts.
Exit: complete lead-to-opportunity workflows pass end-to-end tests, including retries, concurrent validation attempts, disqualification and nurture reactivation.

## Phase 5 — Opportunities, ownership, values and partners
Estimated effort: 7–10 working days. Dependency: Phase 4.
1. Build the eight-stage pipeline, accessible stage movement, list filters and complete Opportunity Detail.
2. Implement need/scope, primary contact/stakeholders, per-deal team roles, commercial owner and required pre-sales roles.
3. Implement handoffs, future-date entry validation, overdue visibility, blocker history, escalation and independent client-engagement dates.
4. Record all seven milestones automatically; preserve event history through regression and re-entry and document how first-entry timestamps feed reports.
5. Implement append-only value history, fixed record exchange rates, stored local/USD values, authorized rate updates and probability overrides.
6. Add multi-partner terms, evidence, percentage/fixed deductions, net-value calculations and excessive-share warnings. Keep historical inputs sufficient to reproduce forecasts.
7. Add closed-won/lost capture, basic evidence attachment, approval-recorded checkbox and delivery handoff notes.
8. Add on-hold/revisit flow, saved views and all card/header warning states.
Exit: a complete pursuit runs from imported lead to won/lost/on hold with accurate ownership, evidence, net forecast and financial history. Internal notes do not reset staleness.

## Phase 6 — My Work, dashboards, search and reports
Estimated effort: 5–7 working days. Dependency: Phase 5.
1. Deliver My Work, Needs Attention and role-based Home dashboards with drill-down for every aggregate.
2. Build pipeline, monthly/quarterly weighted forecast and lead funnel; apply net USD calculations and exclude on hold/nurture.
3. Add blocker analysis, handoff median timing, outcomes, individual contribution, value erosion and undocumented partner terms reports.
4. Build scoped universal search, saved filters and paginated report/list exports.
5. Add pipeline movement using historical events, including prior expected close dates so slippage can be reconstructed. Clearly distinguish current-state from as-of reporting.
6. Build parameterized report/query services; validate totals against independently calculated fixtures. Define count-based win rate separately from value-weighted metrics.
7. Exercise the weekly 45-minute review with seeded scenarios, then real migration rehearsal data when authorized.
Exit: all dashboard numbers reconcile with underlying permitted records; restricted amounts are not leaked through totals/exports/search. No separate spreadsheet is needed for the review.

## Phase 7 — Pre-sales and document collaboration
Estimated effort: 6–8 working days. Dependency: Phase 5; reporting hooks integrate with Phase 6.
1. Build request creation, queue, assignment/acceptance, contributor management and all nine statuses.
2. Add needed-by and customer meeting dates, effort estimates/actuals, blockers, weekly workload and request deliverables.
3. Implement review/share approval. Separate artifact-sharing approval from the non-gating external commercial approval record.
4. Complete file/link/email artifact metadata, versioning, superseded versions, internal-only controls and company/deal client-shared registers.
5. Build Outlook add-in linking/classification and attachment registration through Microsoft Graph. Use least-privilege scopes, protected token storage, idempotent link/import and retry handling.
6. Add SharePoint/OneDrive access-error states, stale/deleted link handling and safe downloads; avoid public file URLs.
7. Add reusable asset search, pre-sales cost and partner performance views.
Exit: requested work reaches approved/delivered, the exact recipients/date are recorded, and Outlook linking registers attachments without a second upload. Real Graph acceptance requires the connected environment.

## Phase 8 — Automation, configuration parity and operations
Estimated effort: 3–5 working days. Dependency: Phases 5–7.
1. Complete all exception notifications with preferences, deduplication, escalation recipients and in-app read/unread state. Add email delivery only through an approved channel; a local mail sink is for testing only.
2. Schedule due actions, overdue holdings/blockers, stale engagement, validation delays, missing proposal follow-up, pre-sales/close deadlines and revisit reminders.
3. Implement monthly rate refresh, failure/large-movement alerts, administrator override and confirmed selective re-baseline. Store source and refresh metadata.
4. Add weekly leadership summary and scheduled reports with permissions reevaluated at delivery time.
5. Add rate/job status administration, failed-job visibility and safe replay.
6. Create sanitized configuration export/comparison for US/International and documented reconciliation without connecting their client databases.
Exit: time-controlled tests prove jobs run once, retry safely and do not generate alert storms or deliver unauthorized data.

## Phase 9 — AI assistance with human confirmation
Estimated effort: 5–7 working days. Dependency: trustworthy activity data and completed access controls; enablement is data-gated, not merely date-gated.
1. Build the internal AI interface and approved Azure provider adapter; local fixtures are clearly labeled demonstrations.
2. Implement pursuit summaries, meeting summaries, extraction, suggested field changes, pipeline risk assistance and meeting account briefs.
3. Use structured response validation, source-record references, request limits and clear unavailable/error states.
4. Show a review/diff interface. Apply only explicitly accepted changes, then rerun domain validation and record the acceptance audit.
5. Treat emails/documents as untrusted content, enforce user/tenant/restriction boundaries and prevent document instructions from invoking application actions.
6. Add evaluation fixtures, hallucination/grounding checks, acceptance metrics, latency/cost visibility and retention/redaction controls.
Exit: no silent writes or unauthorized context; useful evaluations pass and real-user acceptance is measured against the PRD’s above-50% target before broad rollout.

## Phase 10 — Hardening, migration and acceptance
Estimated effort: 5–7 working days, with testing already continuous throughout the build.
1. Run integration/end-to-end tests for every FR and all 19 original acceptance criteria across both instance types.
2. Test restricted-field inference, IDOR, CSRF, session expiry, file access, export injection, cross-tenant background jobs, concurrent edits, duplicate conversion and audit tampering resistance.
3. Run keyboard/screen-reader checks, automated accessibility checks, responsive browser tests and visual regression checks for key screens.
4. Load test 20,000 contacts, 5,000 leads and 5,000 opportunities on a documented hardware profile. Meet board/list under 2 seconds and report under 4 seconds; report percentile and conditions, not an unexplained average.
5. Rehearse migrations with dry runs, record counts, money-total reconciliation and source attribution checks. Import open pipeline/contacts plus the agreed closed history.
6. Verify daily backup, 30-day retention, restore into a clean instance and both database/file consistency. Measure restore time; agree recovery objectives before production.
7. Resolve critical security/usability defects; document known limitations, operator runbooks and onboarding.
Exit: business owner runs the full weekly review, all critical paths pass and migration/restore are demonstrated. Freeze the old tracker according to the agreed cutover plan.

## Phase 11 — Repeatable local Docker release
Estimated effort: 2–3 working days. Dependency: relevant feature gates above.
1. Publish reproducible images and development/release Compose configurations, with image versions/digests and dependency inventory.
2. Add bootstrap scripts that validate environment, generate local-only secrets, create persistent volumes, migrate and seed synthetic data once.
3. Package two deployment variants: local-demo (local OIDC, local file storage, fixture AI) and connected (real Entra, Graph, SharePoint and Azure AI configuration).
4. Run independent Compose projects for US and International, with separate databases, Redis instances, storage, credentials and job schedulers. The local defaults are US 8083 and International 8082.
5. Use local TLS where needed for Outlook/OIDC browser requirements; document local certificate trust. Plain loopback demo HTTP is not production transport-security acceptance.
6. Verify fresh-machine setup, stop/start persistence, safe image upgrades, migration recovery, backup/restore and complete smoke tests.
7. Deliver the README, architecture diagram, env reference, demo users, API reference, test report, known limitations and operator guide.
Exit: another developer can clone, configure and start both instances without manual database edits. Production-style local release serves built UI assets, not a Vite development server.

## Local Docker topology and command contract
> Browser → reverse proxy → built React application + /api/v1 → FastAPI
> FastAPI → PostgreSQL; Redis → Celery worker + one scheduler per deployment
> Identity adapter → local OIDC OR Entra ID
> Document adapter → persistent local files OR Microsoft Graph/SharePoint
> AI adapter → labeled fixtures OR approved Azure AI service
Compose starts healthy dependencies before dependents and waits for successful migration completion. PostgreSQL, Redis and internal job ports are not public. Non-root images, resource limits, rotation of logs and environment-specific secrets are part of the release.
Proposed command interface to implement:
> cp .env.example .env
> make bootstrap MODE=local-demo INSTANCE=INTERNATIONAL
> make up MODE=local-demo INSTANCE=INTERNATIONAL PORT=8082
> make smoke INSTANCE=INTERNATIONAL
> make test
> make backup INSTANCE=INTERNATIONAL
> make restore INSTANCE=INTERNATIONAL BACKUP=<verified-backup-path>
> make down INSTANCE=INTERNATIONAL
These commands do not exist yet. Bootstrap must be idempotent, down must preserve volumes, and destructive reset must be a separately named explicit action. Real integration credentials are never shipped in demo seed data.
Do not claim that local fixtures validate Entra sign-in, Outlook/SharePoint permissions, live rates or Azure AI. Each has a separate connected test checklist. Docker on a laptop is the requested deployment endpoint, not proof of production availability or managed encryption/backup compliance.

## Planning estimate and checkpoints
The effort ranges above total approximately 53–75 working days of sequential phase duration before overlap. With two full-time engineers, shared QA/design support and daily business decisions, budget roughly 11–15 calendar weeks for complete scope and acceptance; parallel UI/backend work can shorten the critical path. Re-estimate after the first two phases. External tenant access and AI data readiness can extend connected acceptance independently.
The original two-week target is a core launch aspiration, not an estimate for this complete product. Do not describe the full UI, Microsoft integration, analytics, AI and hardening scope as a two-week build.
| Checkpoint | Demonstrable outcome |
| Foundation | Docker boots, branded UI shell, identity and isolation work. |
| Core workflow | Import → outreach → independent conversion → proposal → close, with ownership and history. |
| Team operations | My Work, reporting, pre-sales, documents, partners and notifications work end to end. |
| Intelligent assistance | AI suggestions are grounded, authorized and explicitly accepted. |
| Release | Both local instances pass acceptance, backup/restore and connected checks where credentials exist. |
Implementation should start with Phase 0 and Phase 1, producing the independent repository, requirements matrix, design tokens and running Docker skeleton.

## Standards and primary references
WCAG 2.2 accessibility recommendation: https://www.w3.org/TR/WCAG22/
OWASP Application Security Verification Standard: https://owasp.org/www-project-application-security-verification-standard/
Docker Compose startup and health dependencies: https://docs.docker.com/compose/how-tos/startup-order/
FastAPI releases: https://github.com/fastapi/fastapi/releases
Business scope source: Soothsayer_CRM_Requirements_v4.0.docx supplied by the user. ATPLCRM name, colours and local Docker endpoint come from the user’s subsequent request. Architecture, effort estimates and sequencing in this plan are recommendations.
