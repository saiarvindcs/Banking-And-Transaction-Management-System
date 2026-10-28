# Seven-phase delivery matrix — implemented versus missing

| Phase | Implemented | Still required before claiming completion |
|---|---|---|
| 1 Banking foundation | Django DRF, PostgreSQL settings, JWT login, roles, account/beneficiary models, Swagger, Docker | MFA verification, verified beneficiary flow, account opening workflow, secure provisioning |
| 2 Transaction engine | Internal transfer service, double-entry transfer journals, idempotency, ordered row locks, F updates, limits, basic risk alerts, audit events | General ledger/chart of accounts, append-only enforcement, detailed fraud engine, full reconciliation, approval workflows, deposits/withdrawals |
| 3 Distributed processing | Redis/Celery wiring, outbox model and demo dispatcher | Actual provider notifications, websocket events, retry/dead-letter handling, exactly-once consumer semantics, metrics |
| 4 Full stack | React customer portal, accounts, transfers, history, staff overview | Production UI, complete operations console, accessibility audit, pagination UX, refresh-token handling |
| 5 Banking products | Loan/card/bill data models and read-only API | Loan servicing, EMI posting, authorization/capture/reversal, real bill processing, recurring payments |
| 6 Investments and final engineering | Holdings model/read-only API, sample tests, CI workflow | Order execution simulation, valuations, full coverage, security hardening, performance testing |
| 7 Production readiness | Security setting baseline, CI checks, docs | Independent audit, regulatory gap assessment, KYC/AML controls, encryption key management, HA, backup/restore drills, monitoring, penetration testing, cloud hardening, incident response |

Do not present unimplemented modules as complete. No real banking license or payment rail integration exists.
