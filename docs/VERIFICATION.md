# ATPLCRM v0.8 verification

Verified locally on 13 September 2026.

| Check | Result |
|---|---|
| Commercial API workflow tests | 2 passed: partner deductions/net value and report; USD rate guard and probability snapshot |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| Commercial workspace browser check | Passed: authenticated pipeline detail opened, Commercial tab rendered, partner action available |
| International deployment | Healthy; API `0.8.0`; migration `0007_commercial` |
| US deployment | Healthy; API `0.8.0`; migration `0007_commercial` |
| Background worker | Registered monthly FX refresh, 15-minute exception scan and Monday summary tasks |
| Fresh database migration | Disposable PostgreSQL database upgraded from empty through `0007_commercial` and was removed |
| Python source | Commercial API, models, schemas, tasks and migration compiled successfully |

The v0.8 focused checks cover the new financial invariants without repeating the whole established suite. The prior v0.7 baseline recorded 31 API tests, a 9-test isolated Chrome suite, Work/Attention notification acceptance, both local deployments and immutable audit/value/action history guards.

The monthly rate adapter is implemented and fails visibly when `FX_RATES_URL` is absent. Connected acceptance remains pending until the business selects and approves a published source whose JSON endpoint supplies `effective_date` and `rates_to_usd`.
