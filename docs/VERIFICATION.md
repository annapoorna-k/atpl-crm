# ATPLCRM v0.11 verification

Verified locally on 15 September 2026.

| Check | Result |
|---|---|
| Lead and pipeline API workflows | 11 passed: action completion/history, stale-version rejection, future dates, stage evidence/concurrency, seven milestones, working calendar, movement analysis, opportunity editing, advanced filters, saved views, bulk assignment and stakeholders |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| International deployment | Healthy on `http://localhost:8082`; API `0.11.0`; migration `0010_pipeline_completion` |
| US deployment | Healthy on `http://localhost:8083`; API `0.11.0`; migration `0010_pipeline_completion` |
| New pipeline controls | Eligible-validator route, qualified opportunity patch, lead/opportunity advanced filters, calendar-aware elapsed days and management movement report are live in both API schemas |
| Python source | API, models, schemas and migration compile in the application image |

These are focused Feature 5 checks and avoid repeating the established full suite. The v0.10 verification covered import/data-quality; earlier releases cover company/contact/activity, commercial, authorization and browser acceptance.

The local release now completes the PRD lead and opportunity workflow scope. Connected-scale performance, production identity and other remaining release-hardening work are tracked separately in the implementation status.
