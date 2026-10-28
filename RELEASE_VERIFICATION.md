# Banking & Transaction Management — Single Consolidated Release

This release is based on `Banking_Transaction_Management_Integrated_Development_Startup_Fixed(2).zip` (the user's previously tested project). The existing API and Django Templates files were retained except where necessary for the agreed fixes. It is a simulated portfolio application, not production banking software.

## Included changes

| ID | Implemented source change |
| --- | --- |
| BUG-002 | Django password validators enforced on API registration; 10-character minimum. |
| BUG-004 | Docker image builds initial Django migrations, and targeted `repair_legacy_loanpayment` command repairs the specific missing legacy table after `migrate`. |
| BUG-005 | Reconciliation iterator now specifies `chunk_size=1000`. |
| BUG-007 | Blocked cards cannot be reactivated or frozen; state transitions are protected by row locks. |
| FEAT-001 | Staff-only `POST /api/v1/operations/withdrawals/`; atomic, balanced ledger, unique reference, insufficient funds check. |
| FEAT-002 | Staff-only `POST /api/v1/transfers/{id}/reverse/`; compensating journal; original transfer and journal unchanged; duplicate prevention. |
| IMP-001 | Correct beneficiary verification route; deprecated old typo route retained for compatibility. |
| IMP-002/003 | Deterministic bill and investment list pagination. |
| IMP-004 | Staff-only controls removed from customer Products & Payments action list; backend checks retained. |
| IMP-005 | Statement path uses `{id}` in schema, retaining same URL shape. |
| IMP-006 | In-app notifications with audit-triggered outbox, Celery dispatch, recipient-filtered REST list. |

## Verification performed in this environment

- Original-to-release source file comparison, preserving unchanged modules.
- Python compilation of all `.py` source files: passed.
- Archive integrity and release manifest checks: passed.
- Static checks for routes and regression-test presence: passed.

**Not executed:** Django runtime checks, pytest integration tests, PostgreSQL/Redis/Celery Docker startup. This environment has neither Docker nor installable Django dependencies. A Python syntax pass is not a substitute for those checks. Therefore this package is **not claimed fully runtime-verified**. No source-code-only process can guarantee a deployment with an unknown existing database state.

## Upgrade without losing existing data

1. Keep your original working folder and Docker named volume. **Never run `docker compose down -v`.**
2. Back up PostgreSQL before upgrading. The new source does not contain your existing DB records.
3. Extract this ZIP to a new directory. From `banking_platform` run `docker compose up -d --build` using the **same Compose project name** as your original deployment if you intend to reuse its volume. Running from a differently named directory may create a separate volume and show an empty database; this does **not** mean data was deleted. You can set `docker compose -p <original_project_name> ...` explicitly.
4. Verify `docker compose exec api python manage.py check` and `docker compose exec api python manage.py showmigrations`.
5. Run `docker compose exec api pytest -q` (pytest is installed by requirements.txt). Do not switch production traffic until tests pass.
6. Test **only the changed endpoints** and the high-risk flows; do not repeat the entire day's manual Swagger walkthrough.

### Known migration history nuance

The provided original ZIP has only migration `__init__.py` files. Its Dockerfile ran `makemigrations` during container startup, so migration `0001_initial` content may have varied over time. This release generates migration files at image build time and provides a narrowly targeted repair for the confirmed missing `loans_loanpayment` table. If an existing database has **other** missing tables or incompatible migration state, inspect the failure before changing migration history. Do not fake/unapply migrations or delete volumes.

### Sample new requests

Staff withdrawal: `POST /api/v1/operations/withdrawals/` with `{"account":"<UUID>","amount":"100.00","reference":"WITHDRAW-TEST-001"}`.

Staff reversal: `POST /api/v1/transfers/<UUID>/reverse/` with no body. Only completed transfers are reversible, and the destination must have enough funds.

Customer notifications: `GET /api/v1/notifications/` with JWT bearer token.
