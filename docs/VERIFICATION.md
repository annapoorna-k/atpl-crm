# ATPLCRM v0.5 verification

Verified locally on 12 September 2026.

| Check | Result |
|---|---|
| FastAPI workflow, administration, data-tools and productivity suite | 23 passed |
| React formatting | Passed |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| Isolated Chrome acceptance suite | 8 passed |
| International Chrome acceptance suite | 8 passed |
| US Chrome acceptance suite | 8 passed |
| Health and API version | HTTP 200 and `0.5.0` on both instances |
| PostgreSQL migration | `0004_productivity` on both instances |
| Tenant/currency isolation | International: AED, BHD, EUR, GBP, INR, SAR, USD; US: USD only |
| Runtime services | API, database, Redis, scheduler, web and worker running in both instances |

The browser suite covers all routes, opportunity detail/timeline/value views, lead creation and independent conversion, phone layout, administrator management, validated import and search, CSRF recovery, personal saved views, manager bulk assignment, and opportunity stakeholder creation/editing. The API suite additionally covers saved-view privacy, server pagination/filtering/sorting, bulk-assignment authorization and optimistic conflicts, same-company stakeholder enforcement, role updates, removal, and primary-contact protection.

Before upgrading persistent local deployments, PostgreSQL dumps are stored in the ignored `backups/` directory. International and US post-deployment health, migration, tenant/currency isolation and full browser results are recorded as part of each local release operation.
