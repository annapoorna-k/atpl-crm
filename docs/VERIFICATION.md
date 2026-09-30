# ATPLCRM v0.16 verification

Full release verification completed on 16 September 2026. Documentation and deployed-health status were refreshed on 30 September 2026.

| Check | Result |
|---|---|
| API regression | 46 tests passed; authentication, CSRF, role gates, lead/pipeline concurrency, commercial, contacts/activity, imports/data quality, documents, pre-sales, notifications and reporting |
| Demo-readiness focus | 4 tests passed for permission contract, management data gates, ranked/recent search, login throttling and bounded bootstrap metadata |
| TypeScript and Vite production build | Passed; 1,585 modules transformed, including global search, dashboard visuals, lead drag-and-drop and scrollable navigation |
| Clean PostgreSQL install | Passed from an empty disposable volume through `0013_demo_readiness`; older index migrations made idempotent |
| Disposable scale profile | Passed with 20,006 contacts, 5,000 scale leads and 5,000 scale opportunities; see `PERFORMANCE_ACCEPTANCE.md` and `performance-v0.15.json` |
| International deployment | Healthy at `http://localhost:8082`; API `0.16.0`; migration `0013_demo_readiness` |
| US deployment | Healthy at `http://localhost:8083`; API `0.16.0`; migration `0013_demo_readiness` |
| Deployment safety | Separate pre-deployment PostgreSQL backups created for International and US; disposable scale containers/volumes removed after measurement |
| Focused v0.16 reporting contract | 1 test passed; role dashboards and governed exports |
| v0.16 UI follow-up | Production build passed; lead active-status drag-and-drop and independently scrollable side navigation deployed to both editions |
| Python source and migration syntax | Passed |

The regression pass found and fixed a pre-existing missing working-calendar initialization in the Needs Attention queue. The clean-install pass found and fixed duplicate-index failures caused when the baseline had already created current model indexes.

The release is suitable for a local client demonstration with synthetic data. Connected Entra identity, Graph/Azure adapters, production concurrency testing, production accessibility certification and Azure deployment remain outside this release.
