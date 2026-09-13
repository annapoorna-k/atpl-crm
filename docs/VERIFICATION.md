# ATPLCRM v0.9 verification

Verified locally on 13 September 2026.

| Check | Result |
|---|---|
| Relationship/activity API workflow tests | 2 passed: full contact/source fields, engagement and first-touch derivation, owner collision context/notification, do-not-contact override, protected scoped pagination and backdated order |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| International deployment | Healthy; API `0.9.0`; migration `0008_relationship` |
| US deployment | Healthy; API `0.9.0`; migration `0008_relationship` |
| Live API contract | `/api/v1/activities/` exposes paginated relationship history |
| Python source | API, models, presenters, schemas and migration compile inside the application image |

These are focused Feature 3 checks. They avoid repeating the established full browser/API suite. The prior v0.8 verification covers commercial workflows, both isolated deployments and fresh migration, while the v0.7 baseline records the broader API and Chrome acceptance suite.

Relationship history pagination is enforced in PostgreSQL with tenant and restricted-opportunity authorization in the query. The PRD-scale performance benchmark remains a separate release-hardening activity.
