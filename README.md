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

This is **v0.7, an initial working core**, using synthetic data and local password sign-in. It is not the complete PRD or a production-ready release. Microsoft sign-in is not yet implemented. `APP_MODE=connected` fails closed for demo password login; do not expose this local-demo stack publicly or use real client data until connected identity and production hardening are delivered.

## Working features

- Branded responsive overview, My Work, Needs Attention, lead/opportunity boards and lists, company/contact detail, pre-sales queue, basic reports and read-only configuration overview.
- Database-backed company/contact creation and editing, lead creation, status changes, independent validation, nurture/disqualification and idempotent conversion.
- Shared pursuit context preserves the original lead, source, contacts, team and timeline while keeping Lead and Opportunity separate objects and board populations.
- Ball in Court, atomic action completion and future handoff, immutable completed-action history, blocker owner/resolution, optimistic concurrency, stale/overdue flags and client-only interaction tracking.
- Drag-and-drop and accessible-select opportunity stage changes with evidence prompts, row locking and version-conflict protection; required pre-sales roles; won/lost/hold validation; probability overrides; restricted commercial values and append-only value history.
- Seven-milestone lifecycle tracking on every pursuit, plus count, median working-day and health-target reporting.
- Server-backed My Work queues for overdue, today and upcoming actions, blockers owned by the user, and assigned pre-sales deliverables.
- Needs Attention exception queue for overdue or missing actions, long-held pursuits, aged blockers, client inactivity, expired close dates, delayed validation and overdue deliverables.
- Per-user notification preferences and thresholds, durable in-app delivery history, escalation routing, 15-minute exception scans, Monday leadership summaries, and automation run/failure monitoring.
- Team assignments, pre-sales request creation/status updates, secure document-link registration, basic contact collision notifications and periodic attention/revisit notifications.
- Administrator-managed local users, access levels, activation and password resets, plus configurable workflow labels, stage probabilities and exchange rates.
- Tenant-scoped global search, mapped CSV previews and imports for companies, contacts and leads, downloadable templates/error reports, import history, exact-match duplicate review/merge and a data-quality dashboard.
- Server-paginated company, contact, lead and opportunity lists with search, owner, workflow, priority, country and sort controls; reusable personal saved views; manager-only bulk owner/Ball-in-Court assignment with audit and concurrent-edit protection.
- Editable opportunity stakeholders with company-bound contact selection, relationship roles, and protection against removing the active primary contact.
- Net USD pipeline and weighted totals, lead status distribution, CSV forecast export with spreadsheet-injection escaping.
- Tenant-scoped APIs, session/CSRF protection, non-root app/web containers, persistent database/queue volumes, migration-before-start dependencies.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for limitations and remaining phases. The dashboard bootstrap API is intended for the seeded/early dataset; full activity pagination, analytics and scale benchmarks are still required.

Before approving a local release, use the [manual end-to-end testing handbook](docs/ATPLCRM_MANUAL_E2E_TESTING.md). An editable Word copy with embedded UI screenshots is available at `docs/ATPLCRM_v0.7_Manual_E2E_Testing_Handbook.docx`.

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

## Operate

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
