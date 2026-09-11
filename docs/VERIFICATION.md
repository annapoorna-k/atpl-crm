# ATPLCRM v0.4.1 verification

Verified locally on 11 September 2026.

| Check | Result |
|---|---|
| FastAPI workflow, administration and data-tools suite in the application container | 18 passed |
| React formatting | Passed |
| TypeScript and Vite production build | Passed, 1,581 modules transformed |
| International Chrome acceptance suite | 6 passed |
| US Chrome acceptance suite | 6 passed |
| International health endpoint | HTTP 200, FastAPI |
| US health endpoint | HTTP 200, FastAPI |
| PostgreSQL migrations | `0003_data` on both instances |
| Configurable workspace references | 81 records on each instance |
| Immutable audit/value-history triggers | 2 present on each database |
| Scheduled reminder calculation | Completed successfully on both instances |

The browser suites cover all current routes, opportunity detail and timeline/value views, lead creation, independent manager conversion, sign-out/sign-in, a 390×844 phone viewport, administrator management of local users/reference data, a validated CSV import followed by universal search, and recovery when another tab rotates the CSRF cookie during login. The API suite additionally covers import access, mappings, row validation/history, search pagination and opportunity filtering, duplicate review/merge, data-quality scoring, administrator permission boundaries, self-lockout protection, reference-data propagation, and the invariant USD base rate.

Both deployments run as separate Compose projects with independent PostgreSQL and Redis volumes. The US database reports tenant `atplcrm-us`, instance type `US`, and USD-only currency configuration. The International database reports tenant `atplcrm-international`, instance type `INTERNATIONAL`, and AED, BHD, EUR, GBP, INR, SAR and USD currencies. All API, web, database, Redis, worker and scheduler containers were running after deployment; API and web containers reported healthy.

Pre-data-tools PostgreSQL backups are stored in the ignored local `backups/` directory as `international-before-data-v0.4.dump` and `us-before-data-v0.4.dump`. Earlier pre-administration backups are retained. Acceptance testing uses synthetic data and adds uniquely named test leads/opportunities, companies and local users; each deployed instance therefore has one successful acceptance import in its import history.
