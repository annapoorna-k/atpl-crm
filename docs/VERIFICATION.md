# ATPLCRM v0.12 verification

Verified locally on 15 September 2026.

| Check | Result |
|---|---|
| Complete pre-sales workflow | 1 focused end-to-end API test passed: Head assignment, invalid-transition rejection, tech-lead acceptance, contributors, progress, artifact evidence, Ready for review, Manager approval, delivery, actual effort, share timestamp, weekly queue and cost grouping |
| TypeScript and Vite production build | Passed, 1,582 modules transformed |
| International deployment | Healthy on `http://localhost:8082`; API `0.12.0`; migration `0011_presales_completion` |
| US deployment | Healthy on `http://localhost:8083`; API `0.12.0`; migration `0011_presales_completion` |
| New pre-sales APIs | Request detail/permissions, filtered weekly queue, capacity calculation and management cost report are live in both API schemas |
| Python source | API, models, schemas and migration compile in the application image |

This is a focused Feature 6 check and avoids repeating the established suite. The v0.11 verification covered lead/pipeline completion; earlier releases cover imports, relationships, commercial workflows, authorization and browser acceptance.

The local release now completes FR-75 through FR-81. Connected-scale performance, production identity and other remaining release-hardening work are tracked separately in the implementation status.
