# Banking project — integrated development build

This is a simulated banking project, NOT a licensed, production-ready banking system.

## Added in this package
- Loan disbursement and scheduled-total repayment endpoints with double-entry journal posting.
- Products & payments Django Templates console at `/products/` with forms for existing backend operations.
- LoanPayment persistence model and migration (generate with makemigrations before migrate).

## Important limitations
- Loan repayment is simplified scheduled-total accounting; it is not a full regulated loan servicing engine with accruals, delinquency, penalties or refunds.
- Investments use manually supplied simulated prices, not market feeds.
- Bill payments are simulated; cards do not connect to payment networks.
- The generic product console is for development/testing, not a production UX.
- No third-party KYC, AML, MFA enforcement, banking licensing, security certification, external settlement or verified high availability.
- This build has NOT been end-to-end tested against Docker/PostgreSQL here.

## Run
`docker compose up -d --build` then `docker compose exec api python manage.py makemigrations loans` and `docker compose exec api python manage.py migrate` (only if startup command did not migrate automatically).
Use `/api/docs/` for Swagger and `/products/` for Django Templates actions.
