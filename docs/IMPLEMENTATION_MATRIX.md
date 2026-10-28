# Implementation matrix (evidence-based)

This archive is an enhanced development build based on the supplied ZIP. Do not infer operational certification from the existence of a module.

- Authentication: Django session pages, JWT API login/refresh, role-based staff access. MFA enrollment and challenge are not fully implemented.
- Accounts: customer account creation at zero balance, account listing, beneficiary CRUD.
- Transfers: atomic same-currency internal transfers, sorted account locks, idempotency keys, debit/credit journal, basic limits and risk alert.
- Statements: account ledger entries via API and Django Templates.
- Loans: fixed-rate amortization schedule; no loan disbursement or servicing.
- Cards: read-only card listing; no complete authorization/capture/reversal workflow.
- Billing: read-only payment listing; no bill settlement.
- Investments: read-only holdings; no trading or valuation engine.
- Operations: journal balance checks, audit and risk listings, staff template dashboard.
- Infrastructure: PostgreSQL, Redis, Celery worker, Docker Compose, CI scaffolding.
- Phase 7: hardening settings, security tooling dependencies, docs; no external audit, licensing, or regulatory certification.

Never use this simulator with real funds or payment credentials. End-to-end runtime and financial invariants require independent verification.
