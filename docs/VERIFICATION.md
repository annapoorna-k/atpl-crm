# ATPLCRM v0.14 verification

Verified locally on 16 September 2026.

| Check | Result |
|---|---|
| Reporting workflow | 1 focused API workflow passed: all analytics datasets, seven milestones, lifecycle funnel, movement categories, reconcilable Decimal pipeline total, permission-safe drill-down IDs, Hold exclusion from forecast, role dashboard, report CSV/Excel, full filtered-list CSV/Excel and Standard self-only performance |
| TypeScript and Vite production build | Passed, 1,584 modules transformed |
| International deployment | Healthy on `http://localhost:8082`; API `0.14.0`; migration `0012_documents_register` |
| US deployment | Healthy on `http://localhost:8083`; API `0.14.0`; migration `0012_documents_register` |
| Python source | Reporting router and application entry point compile successfully |

This is a focused reporting completion check. Earlier release verification covers documents, pre-sales, imports, relationships, commercial workflows, authorization and browser acceptance.

The local release completes FR-97 through FR-107, including server-calculated net analytics, shared filters, governed drill-down, role views and CSV/Excel report exports. Azure identity/adapters, scale reconciliation and production hardening remain tracked separately in the implementation status.
