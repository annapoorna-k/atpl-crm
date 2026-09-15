# ATPLCRM Implementation Plan and Azure Target Architecture

**Version 1.1 — corrected for the implemented product and Azure production target**
**Updated:** 13 September 2026
**Product:** ATPLCRM
**Repository:** `/Users/n22/Desktop/ATPLCRM`
**Brand:** dark blue, yellow, grey and white

## 1. Purpose and correction summary

This document is the delivery plan for the independent ATPLCRM product. ATPLCRM has no relationship with Orbit and shares no source code, runtime, credentials, data or release process with it.

The former plan incorrectly named Django and several libraries that are not used. The implemented backend is **FastAPI**, with Pydantic, SQLAlchemy and Alembic. The implemented frontend is **React 19 + TypeScript + Vite**, using custom ATPLCRM CSS and Lucide icons. Production deployment now targets **Microsoft Azure**. Local Docker Compose remains the developer and manual-test environment.

This plan has two explicit views:

1. **As-built baseline (v0.7):** functionality already present and testable in local Docker.
2. **Target state and remaining roadmap:** work required for the complete requirements and an Azure production release.

## 2. Truth at a glance

| Area | Correct position |
|---|---|
| Product boundary | Independent ATPLCRM repository at `/Users/n22/Desktop/ATPLCRM`; no Orbit dependency |
| Current release | v0.11 working core with synthetic local data; lead/pipeline, commercial, company/contact/activity and import/data-quality phases complete locally |
| Web application | React 19, TypeScript, Vite, custom responsive CSS, Lucide icons |
| API | FastAPI 0.135, Pydantic, modular-monolith domain services |
| Persistence | PostgreSQL 17, SQLAlchemy 2, Alembic migrations, decimal financial values |
| Background processing | Celery 5.6 with Redis 7 in local Docker |
| Local edge | Unprivileged Nginx serves the Vite build and proxies same-origin `/api` traffic |
| Local topology | PostgreSQL, Redis, migration, FastAPI, Celery worker, scheduler and web containers |
| Production target | Azure Front Door Premium, Azure Container Apps, PostgreSQL Flexible Server, Azure Managed Redis, Blob Storage, Key Vault and Azure Monitor |
| Identity target | Microsoft Entra ID, OIDC authorization-code flow with PKCE, MFA/Conditional Access |
| Deployment units | Separate International and US regional data planes |
| Kafka | Not required now. Add Event Hubs/Kafka only for a proven ordered, replayable event-stream need |
| Explicitly excluded from baseline | Django, Django REST Framework, AKS/Kubernetes, Elasticsearch and API Management |

## 3. Product scope

ATPLCRM is an internal relationship and pursuit management platform. It must support the complete journey from company/contact capture and outreach, through independent lead validation and opportunity management, to pre-sales delivery, commercial close, reporting and follow-up. It also needs governed administration, auditability, automation, Microsoft collaboration and later human-reviewed AI assistance.

The functional domains are:

- Identity, users, global roles, pursuit roles, field restrictions and tenant/deployment isolation.
- Companies, contacts, outreach activities, consent/do-not-contact and relationship history.
- CSV/Excel import, validation, duplicate review, collision handling and data-quality repair.
- Leads, independent validation, nurture/disqualification, bulk assignment and idempotent conversion.
- Opportunity pipeline, accessible stage movement, concurrency protection, actions, blockers, ownership and seven lifecycle milestones.
- Currency, value history, probability, partner terms, net forecast and close/handoff evidence.
- Pre-sales requests, contributors, effort, review approval, deliverables, capacity and cost.
- Secure artifacts, versions, sharing registers, Outlook linking, SharePoint/OneDrive and reusable assets.
- My Work, Needs Attention, notifications, escalation, scheduled summaries and automation health.
- Search, dashboards, forecasts, funnel, lifecycle, movement, performance and export reporting.
- Azure OpenAI assistance for grounded summaries, extraction and suggestions with explicit human confirmation.
- Administration, configuration parity, monitoring, backup, restore, migration and operational runbooks.

## 4. As-built v0.7 architecture

The current application is a modular monolith. This keeps conversion, audit, financial and authorization changes inside one PostgreSQL transaction boundary while the product is still growing.

```text
Browser
  -> Nginx web container (React/Vite build)
       -> /api/v1 reverse proxy
            -> FastAPI modular monolith
                 -> PostgreSQL 17 (system of record)
                 -> Redis 7 (queue/broker)
                      -> Celery worker
                      -> Celery Beat scheduler

One-shot migrate container -> Alembic -> PostgreSQL
```

Docker Compose currently defines `db`, `redis`, `migrate`, `api`, `worker`, `scheduler` and `web`. The migration container must finish successfully before application services start. PostgreSQL and Redis persist through named volumes. A separate Compose project and `.env.us` provide an isolated US demo instance.

### Current repository structure

```text
ATPLCRM/
├── apps/
│   ├── api/
│   │   ├── atplcrm/          FastAPI routes, services, models, security and jobs
│   │   ├── alembic/          PostgreSQL migrations and audit protections
│   │   └── tests/            API workflow and authorization tests
│   └── web/
│       ├── src/              React UI, API client, types and brand styles
│       └── tests/            Playwright browser acceptance tests
├── infra/                    API/web container and Nginx configuration
├── scripts/                  bootstrap, smoke and backup operations
├── docs/                     status, traceability, verification and test handbook
├── exports/                  shareable project documents and diagrams
├── .github/workflows/ci.yml  current CI workflow
├── compose.yaml
├── Makefile
└── README.md
```

Future Azure infrastructure belongs under `infra/azure/` as Bicep modules and environment parameter files. Microsoft adapters belong under `apps/api/atplcrm/integrations/`; the Outlook add-in can be a separate `apps/outlook-addin/` package. These are target additions, not present-day folders.

## 5. What v0.7 already provides

### Access, security and administration

- Temporary local password login for synthetic demo users, 12-hour inactivity expiry, secure server session and CSRF protection.
- Automatic one-time CSRF refresh and retry when another tab rotates the workspace cookie.
- Tenant-scoped APIs, server-side restricted commercial-value presentation, role checks and immutable audit/value-history protections.
- Administrator user creation/editing, access-level changes, activation/deactivation and password reset.
- Administrator configuration for reference labels/order/availability, stage probability and exchange rates.

### Core CRM and data operations

- Responsive overview, My Work, Needs Attention, companies, contacts, lead board/detail, opportunity board/detail, pre-sales, reports and configuration screens.
- Company/contact create and edit; lead creation, source and linked pursuit context.
- Server-paginated and sorted company, contact, lead and opportunity lists with primary search/filter controls.
- Tenant-scoped universal search with record type, owner, status and country filters.
- Personal saved views and manager bulk owner/Ball-in-Court assignment with optimistic conflict handling.
- Mapped CSV templates, dry-run preview, validation, partial import, error reports and import history for companies, contacts and leads.
- Exact duplicate review/merge, collision warnings and actionable data-quality scoring.

### Lead, pipeline and pursuit workflow

- Independent lead validation, rejection, nurture, disqualification and idempotent lead-to-opportunity conversion.
- Conversion preserves source, team, contacts, activities and history while maintaining separate linked Lead and Opportunity records.
- Opportunity drag-and-drop stage movement plus an accessible select control.
- Evidence capture and stage requirements, row locking, version checks and conflict responses for concurrent movement.
- Atomic action completion: the finished action becomes immutable history and a new owner, action type, description and future due date are required.
- Ball in Court handoff history, structured blockers, client-facing activity dates, stale/overdue warnings and seven lifecycle milestones.
- Opportunity stakeholders with same-company selection, relationship roles and primary-contact protection.
- Restricted values, fixed exchange-rate values, append-only value history, probability override and basic supported partner deduction calculation.

### Work management, pre-sales and reporting

- My Work queues for overdue/today/upcoming actions, owned blockers and assigned pre-sales deliverables.
- Needs Attention exceptions for missing/overdue actions, long-held work, old blockers, client inactivity, expired close dates, delayed validation and late deliverables.
- Per-user notification preferences, durable read/unread history, recipient/escalation rules, 15-minute scans, Monday leadership summaries and automation failure visibility.
- Basic pre-sales request creation, assignment, status and effort handling.
- Secure HTTPS evidence links, net USD pipeline and weighted totals, lead status distribution, lifecycle count/median report and escaped CSV forecast export.

## 6. Target Azure production architecture

![Azure production runtime](architecture/01-azure-production-runtime.png)

### Request and data flow

1. A user opens the regional ATPLCRM hostname over HTTPS. Azure Front Door Premium terminates TLS, applies WAF rules and routes only to the selected regional origin.
2. Front Door reaches the Azure Container Apps environment over Private Link; public access to the Container Apps environment is disabled.
3. The Nginx web container serves the immutable React build. Requests under `/api/v1` remain same-origin and proxy to the internal FastAPI container app.
4. Authentication redirects to Microsoft Entra ID using OIDC authorization code with PKCE. The API validates the callback, maps only provisioned active users and issues a secure, HTTP-only, same-site session cookie. CSRF tokens protect state-changing requests.
5. FastAPI applies deployment scope, record access, field restrictions and business validation before database or integration access.
6. FastAPI reads/writes PostgreSQL through a least-privilege runtime role. Alembic runs separately with a migration role; application containers never receive schema-owner credentials.
7. FastAPI enqueues asynchronous work in Azure Managed Redis. Celery workers consume the queue and call the same domain services as synchronous requests. Redis is not a system of record.
8. Azure Container Apps Jobs run Alembic deployment migrations, the 15-minute exception scan and the Monday leadership summary. This avoids a duplicate singleton scheduler while retaining the current scheduled domain functions.
9. Blob Storage holds approved imports, generated exports and managed artifacts. Private endpoints, versioning, lifecycle rules and blob/container soft delete apply.
10. Workloads authenticate to Azure services with managed identities. Key Vault stores connection secrets or certificates that cannot use identity-based access; secrets never enter images or Git history.
11. OpenTelemetry data flows to Application Insights and Log Analytics. Alerts cover availability, latency, error rates, authentication failure, job failure/backlog, database health, backup, storage and suspicious access.
12. Later Microsoft Graph adapters link Outlook mail/attachments and SharePoint/OneDrive items using least-privilege delegated/application permissions. Later Azure OpenAI calls use approved regions, private networking and only permitted/redacted context; every proposed data change requires human review.

### Azure component responsibilities

| Component | Responsibility | Production rule |
|---|---|---|
| Azure Front Door Premium + WAF | Global edge, TLS, regional hostname routing and web protection | Only configured hostnames/origins; WAF in prevention mode after tuning |
| Azure Container Apps | Nginx/React web, FastAPI API and Celery worker | Web is the sole origin ingress; API and worker stay internal |
| Container Apps Jobs | Alembic migration, exception scan and weekly summary | One execution per deployment/schedule; retries are idempotent |
| PostgreSQL Flexible Server | Authoritative CRM, audit and financial data | Private endpoint, HA where supported, PITR, separate runtime/migration roles |
| Azure Managed Redis | Celery broker and short-lived queue state | TLS/private access; no authoritative business records |
| Blob Storage | Imports, exports, artifacts and versions | Private endpoint; encryption, versioning, soft delete and lifecycle controls |
| Key Vault | Secrets, keys and certificates | Managed-identity access, RBAC, rotation and audit logging |
| Microsoft Entra ID | Workforce identity and access policy | MFA/Conditional Access; provisioned active user mapping; no demo login |
| Application Insights + Log Analytics | Traces, metrics, logs, dashboards and alerts | Correlation IDs and PII/secret redaction; regional retention policy |
| Container Registry | Immutable application images and SBOMs | Pull by digest via managed identity; scan and retention policy |
| Microsoft Graph | Outlook and SharePoint/OneDrive integration | Least privilege, consent governance, idempotency and access-error handling |
| Azure OpenAI | Human-reviewed CRM assistance | Private endpoint, approved model/region, grounding, evaluation and no silent writes |

### Network and trust boundaries

- Separate production virtual networks and private DNS zones for each regional deployment.
- Front Door Premium uses Private Link to the Container Apps origin. Origin public network access is disabled and direct-origin requests are rejected.
- PostgreSQL, Redis, Blob Storage and Key Vault use private endpoints and have public access disabled after deployment validation.
- Network Security Groups and private DNS restrict east-west paths to the minimum required flow.
- Admin access uses Entra-authenticated management and just-in-time elevation; no database or container management port is exposed to the public internet.
- Development, test, staging and production use separate subscriptions or resource groups, identities, databases, storage, secrets and Front Door routes.

## 7. US and International data isolation

![Regional deployment isolation](architecture/02-azure-instance-isolation.png)

ATPLCRM requires two independently operated data planes. “International” and “US” regions must be selected through the data-residency and legal review; the diagram deliberately uses approved-region placeholders.

Each data plane has its own Container Apps environment, PostgreSQL server/database, Managed Redis instance, Blob Storage account/containers, Key Vault, private endpoints/DNS, managed identities, sessions, scheduler/jobs, telemetry workspace, backup set and encryption policy. A deployment never queries or joins the other deployment’s client data.

Container images, Bicep modules and release policy may be shared. Shared operational dashboards may contain service health and non-client aggregates only. They must not receive CRM records, restricted fields, document content, user-entered notes or raw query payloads.

Regional hostnames and cookies use distinct scopes. A user provisioned in both deployments signs in separately and receives a separate session. Configuration parity is maintained through sanitized configuration export/comparison, never through a database link.

## 8. Identity, authorization and audit design

The production login flow is Entra authorization code with PKCE. Entra authentication proves identity; ATPLCRM still decides whether that identity is provisioned, active and permitted for a deployment.

Authorization is enforced in the FastAPI service and repository queries for every read, write, search, export, dashboard aggregate, notification, file link and AI context. React hides unavailable actions for usability but never acts as the security boundary.

Required controls include global access levels, pursuit team roles, owner/manager scopes, restricted commercial fields, independent-validator separation, administrator functions and per-deployment membership. Object IDs alone never grant access. Changes to users, access, stages, rates, values, roles, stage evidence, exports, sharing and AI-accepted suggestions are audited.

Audit and value histories are append-only for the runtime role. Records use optimistic versions for interactive edits and database row locks/transactions for critical transitions. Correlation IDs link UI requests, API logs, jobs and audit events without logging passwords, tokens, document content or unnecessary personal data.

## 9. Availability, backup and recovery

- Use zone-redundant PostgreSQL high availability where the approved region supports it.
- Configure PostgreSQL point-in-time restore and automated backup retention. If policy requires retention beyond the service’s operational limit, add Azure Backup vaulted retention.
- Enable Blob versioning, blob soft delete and container soft delete; lifecycle older versions according to the retention policy.
- Container Apps uses at least two production replicas for web/API where load and budget permit, health/readiness probes, autoscaling and graceful shutdown. The worker scales by queue depth; scheduled jobs enforce single logical execution through idempotency keys/database locks.
- Front Door health probes stop routing to unhealthy origins. Multi-region disaster recovery is a separate approved design because US/International deployments are residency boundaries, not mutual DR replicas.
- Define business-approved RPO/RTO before go-live. Rehearse restore to an isolated recovery environment and reconcile record counts, money totals, audit history and artifacts.

## 10. Observability and operations

Emit structured JSON logs with deployment, environment, correlation ID, route/job name and outcome. Redact authorization headers, cookies, tokens, passwords, document bodies and sensitive free text.

Dashboards and alerts cover Front Door/WAF, Container Apps availability and revisions, request p50/p95/p99, 4xx/5xx rates, Entra callback errors, CSRF/session failures, PostgreSQL connections/storage/replication, Redis memory/latency, queue age, job failures, missing schedule executions, import/export failures and backup health.

Runbooks must cover login outage, high error rate, stuck worker queue, failed migration, database failover, storage access failure, notification storm, compromised user, secret rotation, restore, regional cutover and rollback. Alert ownership and severity targets are required before production.

## 11. Secure CI/CD and deployment flow

![Azure CI/CD and rollback](architecture/03-azure-cicd-release.png)

1. Pull requests require review and run formatting, focused API tests, UI production build, browser acceptance checks where relevant, migration validation, dependency/secret scanning and static security checks.
2. GitHub Actions builds the API/worker/job image and Nginx/React image, records an SBOM and tags artifacts with the commit SHA.
3. GitHub Actions uses workload identity federation/OIDC for short-lived Azure credentials. Long-lived Azure client secrets are not stored in GitHub.
4. Images are scanned and pushed to Azure Container Registry. Deployments reference immutable digests.
5. Bicep modules deploy or update approved infrastructure with per-environment parameters and policy checks.
6. The release takes/verifies the required backup, runs the Alembic Container Apps Job once with its restricted migration role, and stops on failure.
7. A new Container Apps revision starts with no production traffic. Health, migration, authorization, isolation and smoke checks run against that revision.
8. Traffic shifts in controlled steps while availability, latency and errors are observed. Healthy releases are promoted and recorded with commit, image digest and migration version.
9. A breached release shifts traffic to the prior healthy revision. Database rollback uses a pre-written forward-fix/restore strategy because destructive down-migrations are unsafe.

## 12. Environment and configuration model

Use `local`, `development`, `test`, `staging` and `production` configurations. Local Docker may use generated demo passwords and local HTTP on loopback. All connected environments fail closed when Entra, Key Vault or required private dependencies are unavailable.

Settings are typed and validated at startup. Environment files contain local values only and remain uncommitted. Azure uses managed identity and Key Vault references. Resource names include product, deployment (`intl`/`us`), environment and region. Feature flags may gate unfinished connected integrations, but they cannot bypass authorization, audit or tenancy.

## 13. Phased implementation roadmap

### Phase A — Preserve and document the current v0.7 baseline (complete)

**Delivered:** independent repository, branded responsive UI, FastAPI/PostgreSQL core, local Docker, users/configuration, import/data quality, core lead/opportunity workflow, accessible pipeline, lifecycle milestones, work queues and durable notification automation.

**Exit evidence:** local Docker starts, the administrator/non-administrator handbook can be executed, current API tests/UI build pass, and the requirement matrix marks partial/planned conditions accurately.

### Phase B — Azure foundation and Infrastructure as Code

**Dependencies:** Azure subscriptions, approved US and International regions, DNS ownership, budget and naming/tagging policy.

**Deliverables:** Bicep modules for resource groups, networks/private DNS, Front Door Premium/WAF, Container Apps environments/apps/jobs, ACR, PostgreSQL, Managed Redis, Storage, Key Vault, Monitor and private endpoints; environment parameter files; cost budgets; staging deployment; backup and smoke gates.

**Exit:** staging deploys from a clean subscription through GitHub OIDC, public origin/data endpoints are closed, images run by digest and an operator can deploy and roll back using the runbook.

### Phase C — Entra identity, authorization completion and database privilege separation

**Dependencies:** Entra app registrations, tenant admin consent and final role matrix.

**Deliverables:** OIDC+PKCE, provisioned-user lifecycle, MFA/Conditional Access alignment, login throttling, field/record/export/search/notification/AI authorization, restricted-value inference tests, runtime versus migration roles and complete audit before/after coverage.

**Exit:** demo password login is impossible in connected mode; all roles pass the access matrix; self-validation, cross-deployment access, IDOR and restricted-value leakage are rejected and audited.

### Phase D — Complete data capture, imports and relationship history

**Dependencies:** approved field dictionary, retention rules and import templates.

**Deliverables:** remaining company/contact/opportunity fields, full paginated histories, contact engagement updates, consent/do-not-contact controls, Excel import, large background import, fuzzy duplicate candidates, field-level merge selection and prior-touch collision context.

**Exit:** representative 20,000-contact migration dry run reconciles counts and errors; users can repair duplicates without losing ownership, source, activities or audit history.

### Phase E — Commercial, partner, currency and closure workflows

**Dependencies:** approved partner formulas, FX source/refresh policy, probability snapshot rule and close/handoff evidence rules.

**Deliverables:** complete partner terms/evidence UI, fixed/contract/margin calculations, provisional unknown-term handling, net local/USD values, rate refresh/alert/override/rebaseline, historical reproducibility, won/lost reasons, approval record, delivery handoff and specialized pipeline filters/calendars.

**Exit:** every forecast total can be reproduced from stored historical inputs; unsupported partner terms cannot inflate the forecast; close and handoff evidence are complete.

### Phase F — Pre-sales and Microsoft document collaboration

**Dependencies:** completed core pipeline, Graph/SharePoint tenant access and permission approval.

**Deliverables:** full nine-state request matrix, acceptance/review gates, contributors, needed-by/meeting dates, estimates/actuals, capacity and cost; managed artifact upload/link/email metadata; version/supersession; sharing approval, recipients/date/register; reusable library; Outlook add-in and Graph integration.

**Exit:** a request reaches approved/delivered with effort and review evidence, and an Outlook/SharePoint artifact can be registered, versioned, permission-checked and shared without a second uncontrolled copy.

### Phase G — Complete analytics, search and exports

**Dependencies:** commercial rules and reliable historical events.

**Deliverables:** monthly/quarterly pipeline and forecast, historical funnel, loss/blocker/value-erosion/partner/movement analysis, individual contribution, role dashboards, as-of/slippage reporting, ranked PostgreSQL full-text search, complete server-side CSV/Excel exports and sanitized regional configuration comparison.

**Exit:** drill-down totals reconcile with independently calculated fixtures; permissions apply to aggregates and exports; the weekly leadership review requires no side spreadsheet.

### Phase H — AI assistance with explicit human confirmation

**Dependencies:** complete authorization, trustworthy activity/document data, approved Azure OpenAI region/model and privacy review.

**Deliverables:** grounded pursuit/meeting summaries, field extraction, risk assistance and account briefs; structured schema validation; source references; prompt-injection defenses; review/diff interface; accepted-change audit; evaluation, quality, latency and cost monitoring.

**Exit:** no silent write and no unauthorized context; every proposed change is reviewed and revalidated; agreed grounding and user-acceptance measures pass before broad rollout.

### Phase I — Hardening, performance, migration and production cutover

**Dependencies:** all required functional phases and production Azure foundation.

**Deliverables:** WCAG 2.2 AA verification, OWASP ASVS-oriented security evidence, session/CSRF/file/export/audit tests, 20k/5k/5k load profile, restore rehearsal, production migration dry runs, operator/onboarding guides, alert/runbook exercise and controlled cutover.

**Exit:** all critical requirements and acceptance criteria pass in both deployment types; business owners complete the weekly review; recovery objectives are demonstrated; critical security/usability defects are closed; old trackers are frozen under the approved cutover plan.

## 14. Remaining functionality checklist

| Domain | Remaining functionality |
|---|---|
| Identity/security | Real Entra OIDC; provisioned identity lifecycle; fine-grained policy matrix; stronger login throttling; runtime/migration DB privileges; full restricted-data coverage |
| Companies/contacts | Remaining fields and full edits; paginated histories; engagement updates; consent/do-not-contact completion |
| Import/data quality | Excel, background imports over current CSV limit, fuzzy matching, field-level merges and fuller collision context |
| Pipeline | Specialized filters, configurable working calendars and deeper historical movement analysis |
| Commercial | Complete partner agreement fields/evidence/calculations, FX update/rebaseline, probability snapshot rules, won/lost/handoff and approval evidence |
| Documents | Managed upload/storage, Outlook add-in, mail/attachment linking, sharing approval/register, recipients/date, versions and reusable library |
| Pre-sales | Full transitions, review gate/evidence, contributors, individual weekly capacity and cost analytics |
| Reports | Time filters, historical funnel, losses, blockers, erosion, partner/movement/performance, server exports, Excel and configuration parity |
| Search/scale | PostgreSQL full-text indexes/ranking, recent search history, cache strategy and documented performance acceptance |
| Notifications | Current in-app automation is complete; external email/mobile channels only if business scope later requires them |
| AI | Azure OpenAI adapter, grounded experiences, review/consent UI, safety/evaluation and cost/quality monitoring |
| Production | Azure IaC, Entra, private networking, monitoring, image controls, backup/restore evidence, accessibility/security/performance acceptance and cutover |

## 15. Quality and acceptance gates

| Gate | Minimum evidence before production |
|---|---|
| Functional | Requirement matrix has no unexplained gaps; admin and non-admin manual journeys pass |
| Security | Role/record/field/tenant tests, IDOR and CSRF checks, secret scan, image/dependency scan, audit-tamper checks and penetration-test findings resolved by severity policy |
| Accessibility | Keyboard, focus, labels, dialogs, errors, screen reader and contrast validated to the WCAG 2.2 AA target |
| Performance | On the agreed Azure sizing, 20k contacts/5k leads/5k opportunities; board/list under 2 seconds and report under 4 seconds at agreed percentiles |
| Reliability | Health/readiness, autoscaling, job idempotency, queue backlog alerts, database failover behavior and monitored revision rollback demonstrated |
| Recovery | Automated backup healthy; PostgreSQL and Blob restore rehearsed; record counts, totals, history and artifacts reconciled; RPO/RTO accepted |
| Residency | US and International resource/data/session/log boundaries inspected; cross-deployment test access rejected |
| Operations | Dashboards, alert owners, runbooks, on-call path, support ownership, cost budgets and release/rollback procedure accepted |

## 16. Architectural decisions and triggers

- **FastAPI modular monolith:** keep it while one transaction boundary benefits pursuit workflows. Split a service only after workload, ownership or isolation evidence justifies the operational cost.
- **Azure Container Apps rather than AKS:** the product needs managed container execution, internal ingress, autoscaling and jobs without a Kubernetes control-plane burden.
- **Azure Managed Redis rather than legacy Azure Cache for Redis:** use the current managed service direction for new production design. Redis remains queue infrastructure.
- **No Kafka/Event Hubs now:** add it only when multiple independent consumers require ordered, replayable integration events that transactional outbox plus workers cannot satisfy.
- **No Elasticsearch now:** PostgreSQL filtering/full-text search is sufficient until measured relevance or scale proves otherwise.
- **No API Management in the baseline:** introduce it when ATPLCRM exposes a governed partner/public API, subscription products, complex transformation or independent API lifecycle.
- **Container Apps Jobs rather than Celery Beat in Azure:** scheduled scans and summaries become independently observable, single-purpose jobs; Celery remains for queue-driven work.

## 17. Planning range and checkpoints

The completed v0.7 baseline removes the original foundation and core workflow build from the remaining estimate. A reasonable planning range for the remaining full scope is **36–54 sequential engineering working days**, excluding delays for Azure/Entra/Graph access, security review, stakeholder decisions and production migration windows. Parallel frontend/backend/platform work can reduce calendar duration; use phase exit evidence rather than dates to declare completion.

| Checkpoint | Demonstrable outcome |
|---|---|
| Azure-ready foundation | Staging deploys privately through IaC, OIDC federation, migration job and monitored revision rollout |
| Connected security | Entra login and full authorization/audit matrix pass in both isolated deployments |
| Complete operations | Commercial, pre-sales, documents, analytics and automation satisfy end-to-end business journeys |
| Governed intelligence | Azure OpenAI assistance is grounded, permission-scoped, evaluated and human-confirmed |
| Production acceptance | Migration, performance, accessibility, security, backup/restore, runbooks and cutover pass |

## 18. Primary technical references

- Azure architecture icons: https://learn.microsoft.com/azure/architecture/icons/
- Front Door to Container Apps with Private Link: https://learn.microsoft.com/azure/container-apps/front-door-custom-virtual-network-private-link
- Container Apps private endpoints and DNS: https://learn.microsoft.com/azure/container-apps/private-endpoints-with-dns
- Azure Container Apps Jobs: https://learn.microsoft.com/azure/container-apps/jobs
- PostgreSQL Flexible Server high availability: https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-high-availability
- PostgreSQL point-in-time restore: https://learn.microsoft.com/azure/postgresql/backup-restore/how-to-restore-custom-restore-point
- Azure Backup for PostgreSQL Flexible Server: https://learn.microsoft.com/azure/backup/backup-azure-database-postgresql-flex-overview
- Azure Managed Redis migration/retirement direction: https://learn.microsoft.com/azure/azure-cache-for-redis/retirement-faq
- Container Apps Key Vault secret references: https://learn.microsoft.com/azure/container-apps/manage-secrets
- Entra authorization-code flow with PKCE: https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow
- Container Apps OpenTelemetry agents: https://learn.microsoft.com/azure/container-apps/opentelemetry-agents
- GitHub Actions to Azure with OIDC: https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect
- Container Apps pulling ACR images with managed identity: https://learn.microsoft.com/azure/container-apps/managed-identity-image-pull
- Blob soft delete and version recovery: https://learn.microsoft.com/azure/storage/blobs/soft-delete-blob-overview
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- OWASP Application Security Verification Standard: https://owasp.org/www-project-application-security-verification-standard/

The business scope remains Soothsayer CRM Requirements v4.0 supplied by the user. Implementation status and requirement traceability in this repository are the authority for claims about what v0.7 currently provides.
