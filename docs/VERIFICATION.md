# ATPLCRM v0.10 verification

Verified locally on 13 September 2026.

| Check | Result |
|---|---|
| Import and data-quality API workflows | 8 passed: CSV/Excel parsing, mapping, full contact fields, relationship resolution, role protection, lead dates, exact/fuzzy duplicate resolution, field-level merges, reviewed-distinct decisions, quality filters and pagination |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| International deployment | Healthy on `http://localhost:8082`; API `0.10.0`; migration `0009_import_quality` |
| US deployment | Healthy on `http://localhost:8083`; API `0.10.0`; migration `0009_import_quality` |
| File handling | CSV and unencrypted `.xlsx`, 8 MB and 20,000-row limits, duplicate/blank header rejection, first-worksheet processing and 14 MB reverse-proxy request allowance |
| Python source | API, models, schemas and migration compile in the application image |

These are focused Feature 4 checks and avoid repeating the established full suite. The v0.9 verification covered company, contact and activity workflows; earlier verification covers commercial, pipeline, authorization and browser acceptance.

The importer validates the complete file before writing records, retains row errors and reviewed warnings in history, and scopes reference lookup, duplicate discovery, merge movement and quality reporting to the active tenant. PRD-scale connected-environment performance acceptance remains a release-hardening activity.
