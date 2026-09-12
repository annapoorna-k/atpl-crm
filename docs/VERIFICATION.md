# ATPLCRM v0.6 verification

Verified locally on 12 September 2026.

| Check | Result |
|---|---|
| FastAPI workflow, administration, data-tools, productivity and pipeline suite | 27 passed |
| React formatting | Passed |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| Isolated Chrome acceptance suite | 9 passed |
| International Chrome acceptance suite | 9 passed |
| US Chrome acceptance suite | 9 passed |
| Health and API version | HTTP 200 and `0.6.0` on both instances |
| PostgreSQL migration | `0005_pipeline` on isolated and both persistent instances |
| Immutable database history guards | Audit events, value history and completed actions protected in both PostgreSQL instances |
| Tenant/currency isolation | International: AED, BHD, EUR, GBP, INR, SAR, USD; US: USD only |
| Runtime services | API, database, Redis, scheduler, web and worker running in both instances |

The browser suite covers all routes, opportunity detail/timeline/value views, lead creation and independent conversion, phone layout, administrator management, validated import and search, CSRF recovery, personal saved views, manager bulk assignment, opportunity stakeholder creation/editing, drag-and-drop stage evidence, action completion and seven-milestone views. The API suite additionally covers saved-view privacy, server pagination/filtering/sorting, bulk-assignment authorization and optimistic conflicts, same-company stakeholder enforcement, action history, future handoffs, stage conflicts and the exact seven-milestone contract.

Before upgrading persistent local deployments, PostgreSQL dumps are stored in the ignored `backups/` directory. International and US post-deployment health, migration, tenant/currency isolation and full browser results are recorded as part of each local release operation.
