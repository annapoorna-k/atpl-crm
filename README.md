# ATPLCRM

Independent CRM workspace using dark blue, yellow, grey and white. The stack is React + TypeScript, FastAPI, SQLAlchemy, PostgreSQL, Alembic, Celery/Redis and Docker Compose.

## Start locally

Prerequisites: Docker Desktop with Compose, Python 3 for generating local secrets, and available port 8082.

```sh
cd /Users/n22/Desktop/ATPLCRM
python3 scripts/bootstrap.py
docker compose up -d --build --wait
```

Open **http://localhost:8082**. Sign in as **alex@atplcrm.local**. The password is `DEMO_PASSWORD` in `.env`; bootstrap generates it and never commits it. Other demo users use the same local password: `maya` (sales), `james` (pre-sales manager), `omar` (technical), `sarah` (executive), `admin` (administrator), each at `@atplcrm.local`.

This is **v0.15, a client-demo-ready local release**, using synthetic data and local password sign-in. It is not the complete PRD or a production-ready release. Microsoft sign-in is not yet implemented. `APP_MODE=connected` fails closed for demo password login; do not expose this local-demo stack publicly or use real client data until connected identity and production hardening are delivered.

## Working features

- Branded responsive overview, My Work, Needs Attention, lead/opportunity boards and lists, company/contact detail, pre-sales queue, role-specific home dashboards, management analytics and read-only configuration overview.
- Editable qualified opportunity details and complete company/contact editing, including relationship ownership, source attribution, consent, prescribed engagement status, communication details and do-not-contact control; lead creation, status changes, independent validation, nurture/disqualification and idempotent conversion.
- Shared pursuit context preserves the original lead, source, contacts, team and timeline while keeping Lead and Opportunity separate objects and board populations.
- Ball in Court, atomic action completion and future handoff, immutable completed-action history, blocker owner/resolution, optimistic concurrency, stale/overdue flags and client-only interaction tracking.
- Drag-and-drop and accessible-select opportunity stage changes with evidence prompts, row locking and version-conflict protection; required pre-sales roles; won/lost/hold validation; probability overrides; restricted commercial values and append-only value history.
- Seven-milestone lifecycle tracking on every pursuit, plus configurable working calendars, count, median working-day health targets, and historical stage-movement analysis.
- Server-backed My Work queues for overdue, today and upcoming actions, blockers owned by the user, and assigned pre-sales deliverables.
- Needs Attention exception queue for overdue or missing actions, long-held pursuits, aged blockers, client inactivity, expired close dates, delayed validation and overdue deliverables.
- Per-user notification preferences and thresholds, durable in-app delivery history, escalation routing, 15-minute exception scans, Monday leadership summaries, and automation run/failure monitoring.
- Fast backdated activity entry with derived client-facing behavior, automatic contact engagement/first-touch updates, pre-save cross-owner context and durable collision notifications.
- Company 360 and Contact Detail show complete paginated interaction histories, every related pursuit, source and relationship context, and retained do-not-contact overrides.
- Complete pre-sales delivery management with Head of Pre-Sales assignment, tech-lead acceptance, supporting contributors, evidence-backed review/approval, named delivery recipients, actual effort, weekly capacity and cost analysis.
- Managed private file uploads, SharePoint/OneDrive links, manual selected-email registration with automatic attachment artifacts, approval/share controls, named-recipient client registers, visible version supersession, search and a reusable asset library.
- Administrator-managed local users, access levels, activation and password resets, plus configurable workflow labels, stage probabilities and exchange rates.
- Tenant-scoped global search; mapped CSV and Excel dry runs/imports for companies, full contacts and leads; downloadable templates/error reports; import warnings and durable history; exact/fuzzy duplicate review with field-by-field merge or dismissal; and a filtered, exportable data-quality dashboard.
- Server-paginated company, contact, lead and opportunity lists with complete source, responsibility, activity, blocker, partner, service, close-period and value filters; reusable personal saved views; manager-only bulk owner/Ball-in-Court assignment with audit and concurrent-edit protection.
- Editable opportunity stakeholders with company-bound contact selection, relationship roles, and protection against removing the active primary contact.
- Server-calculated management analytics with date/owner/service/source/country/type filters: net pipeline, monthly and quarterly weighted forecast, historical lead funnel, lifecycle bottlenecks, blockers, grouped win/loss performance, loss reasons, value erosion, movement and individual contribution. Every figure exposes its underlying records, and every report exports safely to CSV or Excel.
- Commercial management for multiple partners, contract/gross-margin/fixed/commission/spread terms, evidence status, share warnings, net local/USD values and partner performance/undocumented-term reporting.
- Per-opportunity fixed-rate updates, administrator rate overrides and confirmed open-deal re-baselining, plus a configurable monthly published-rate adapter with movement and failure alerts.
- Complete Won/Lost evidence capture, project and delivery-handoff fields, optional commercial approval evidence and stored stage-default probability beside overrides.
- Tenant-scoped APIs, session/CSRF protection, non-root app/web containers, persistent database/queue volumes, migration-before-start dependencies.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for limitations and remaining phases. Relationship histories paginate independently; the board/bootstrap payload is capped to the 100 most recently updated pursuits at scale; complete server-paginated lists and search remain available.

Before a client presentation, follow the [client demo guide](docs/CLIENT_DEMO_GUIDE.md). The [local performance acceptance](docs/PERFORMANCE_ACCEPTANCE.md) records the disposable 20k/5k/5k benchmark.

Before approving a local release, use the [manual end-to-end testing handbook](docs/ATPLCRM_MANUAL_E2E_TESTING.md). An editable Word copy with embedded UI screenshots is available at `docs/ATPLCRM_v0.8_Manual_E2E_Testing_Handbook.docx`.

## Verify

```sh
docker compose exec api pytest -q
docker compose run --rm migrate alembic current
docker compose ps
curl http://localhost:8082/api/health/
```

UI build/browser checks require Node 22.12+ and Chrome:

```sh
cd apps/web
npm ci
npm run build
npm run test:e2e
```

Browser workflow testing creates a synthetic acceptance lead/opportunity. Use a disposable local deployment for repeated acceptance suites. Tests read the generated local password from `.env` without printing it.

## Published exchange-rate source

Set `FX_RATES_URL` only after approving a published source. The monthly adapter expects HTTPS JSON with rates expressed as USD per one unit of currency:

```json
{
  "effective_date": "2026-09-01",
  "rates_to_usd": { "AED": 0.272294, "EUR": 1.09, "USD": 1 }
}
```

`FX_RATE_SOURCE` records the human-readable source name. A refresh updates the reference table for future opportunities; existing opportunities keep their stored rate until their commercial owner updates one deal or an Administrator confirms re-baselining of an open selected set.

## Operate

Use the guarded demo operator for health and deliberate reset workflows:

```sh
python3 scripts/demo.py status --instance INTERNATIONAL
python3 scripts/demo.py backup --instance INTERNATIONAL
# destructive, creates a backup first and requires the exact confirmation
python3 scripts/demo.py reset --instance INTERNATIONAL --confirm RESET-ATPLCRM
```

Routine container operations:

```sh
docker compose logs --tail=100 api worker scheduler
docker compose stop
docker compose start
docker compose down
```

`down` retains named volumes. Do not add `-v` unless deliberately destroying demo data. Seeding is idempotent and does not overwrite existing users/data. To upgrade, run `docker compose up -d --build --wait`; review migrations and take a backup first.

## Separate US deployment

Run `python3 scripts/bootstrap.py --instance US` to create `.env.us` with independent secrets and port 8083. Then run `docker compose --env-file .env.us up -d --build --wait`. Open http://localhost:8083 and use the password from `.env.us`. Separate Compose project names isolate databases, queues and volumes. Never change the instance type of an existing populated deployment: the seed/init command rejects it.

## Layout

```text
apps/api/atplcrm/      FastAPI routes, domain model, services and workers
apps/api/alembic/      PostgreSQL schema migrations and audit protections
apps/api/tests/        API workflow and authorization tests
apps/web/src/          Typed React UI, API client and brand styles
apps/web/tests/        Browser acceptance tests
infra/                Dockerfiles and reverse proxy
scripts/              Bootstrap, smoke checks and database backup
docs/                 Architecture, delivery status and verification notes
compose.yaml          Isolated local application stack
```

The API is a modular monolith so lead conversion, audit history, commercial values and permissions share one reliable transaction boundary. Split services only when integrations or workload evidence justify it. Dependency inputs and resolved lockfiles are committed together. ATPLCRM has no dependencies on another platform.
