# Delivery status — expanded banking simulator

This is an **expanded educational banking simulator**, not a licensed bank, audited financial system, or fully production-ready platform.

Implemented in this revision:
- Password validation at registration.
- Static CSS serving with WhiteNoise and collectstatic in Docker image.
- Transfer request schema and Idempotency-Key header in Swagger.
- Staff-only simulated deposit using balanced ledger journal and idempotent reference.
- Staff-only beneficiary verification and transfer validation requiring verification.
- Customer card issuance, freeze, activation and irreversible block.
- Loan application and staff approval (no disbursement/repayment yet).
- Simulated bill payment with account debit and balanced ledger journal (no external settlement).
- Paper investment buy/sell with simulated prices, holding updates and ledger entries (no market feeds).

Known limitations and incomplete functionality:
- Loan disbursement, EMI repayments, **real bill settlement**, **real investment order execution**, and card transaction authorization are **not implemented**.
- Simulated deposit clearing journal uses a clearing account with no balance movement. It is not a real external settlement integration.
- Staff roles must be assigned through Django admin or secure provisioning; public registration always creates CUSTOMER.
- Full MFA enforcement, independent external security audit, production hardening, observability, disaster recovery and regulatory certification are not provided.
- No full PostgreSQL/Docker integration test run was possible in the packaging environment; test in Docker before using even as a demonstration.
- Existing databases should be backed up before deployment; no database schema changes were introduced in this revision.

## Quick start

`docker compose up -d --build`

Visit `http://localhost:8000/api/docs/` and `http://localhost:8000/`.

Run `docker compose exec api python manage.py migrate` if migrating an existing database; for a new database create migrations as documented in README.

**Do not use real customer data or real funds.**
