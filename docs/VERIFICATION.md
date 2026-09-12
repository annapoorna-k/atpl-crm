# ATPLCRM v0.7 verification

Verified locally on 13 September 2026.

| Check | Result |
|---|---|
| FastAPI workflow, administration, data-tools, productivity, pipeline and notification suite | 31 passed |
| React formatting | Passed |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| Isolated Chrome acceptance suite | 9 passed |
| Isolated Work/Attention/notification acceptance journey | 1 passed |
| International Chrome acceptance | Focused Work/Attention/notification journey passed against the persistent deployment |
| US deployment acceptance | Health, application version, migration and service checks passed |
| Health and API version | HTTP 200 and `0.7.0` in isolated, International and US deployments |
| PostgreSQL migration | `0006_notifications` in isolated, International and US databases |
| Immutable database history guards | Audit events, value history and completed actions protected in both PostgreSQL instances |
| Tenant/currency isolation | International: AED, BHD, EUR, GBP, INR, SAR, USD; US: USD only |
| Runtime services | API, database, Redis, scheduler, web and worker running in both instances |

Browser coverage includes all established workflows plus notification preferences, administrator exception scans, automation status, complete My Work sections, Needs Attention exceptions and the durable notification inbox. The API suite additionally verifies preference isolation, recipient routing, durable delivery history, read timestamps, automation runs, weekly-summary deduplication and the complete work-queue contract.

Before this upgrade, PostgreSQL dumps for both persistent deployments were stored in the ignored `backups/` directory. Post-deployment checks confirmed both six-service stacks are running, the scheduler is active, and the worker registered the exception-scan and weekly-summary tasks.
