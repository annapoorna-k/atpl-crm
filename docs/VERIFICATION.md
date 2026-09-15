# ATPLCRM v0.13 verification

Verified locally on 15 September 2026.

| Check | Result |
|---|---|
| Documents and email workflow | 1 focused API workflow passed: link, role-gated approval, named sharing, version conflict, managed upload/download, selected email, automatic attachment registration, shared register and reusable library |
| Recipient-aware pre-sales delivery | Existing focused pre-sales workflow passed with required same-company recipients written to the shared register |
| TypeScript and Vite production build | Passed, 1,583 modules transformed |
| International deployment | Healthy on `http://localhost:8082`; API `0.13.0`; migration `0012_documents_register` |
| US deployment | Healthy on `http://localhost:8083`; API `0.13.0`; migration `0012_documents_register` |
| Outlook package | Manifest/task pane and brand icons are served at `/outlook/`; tenant deployment awaits the approved Azure HTTPS host and Entra configuration |
| Python source | API, models, schemas and migration compile successfully |

This is a focused Feature 7 check. The v0.12 verification covered pre-sales completion; earlier releases cover imports, relationships, commercial workflows, authorization and browser acceptance.

The local release now completes FR-85 and FR-87 through FR-92. FR-86's Outlook task pane is implemented and requires the approved Azure HTTPS/Entra environment for tenant deployment and connected acceptance. Production identity and release hardening remain tracked separately in the implementation status.
