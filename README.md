# Banking & Transaction Management Platform

**Status: functional starter implementation, NOT a complete seven-phase banking system.** See [delivery gaps](docs/PHASES_AND_GAPS.md). This repository includes backend, frontend, Docker, PostgreSQL, Redis/Celery, tests, and CI scaffolding. No real funds or real payment networks are supported.

## Quick start (Docker)

```bash
docker compose up -d --build db redis
# Create database migrations from included models:
docker compose run --rm api python manage.py makemigrations
docker compose run --rm api python manage.py migrate
docker compose up -d --build api worker
docker compose exec api python manage.py createsuperuser
# Optional simulation accounts:
docker compose exec api python manage.py seed_demo
```

The frontend is served by **Django Templates** at `http://localhost:8000/`. No React or Angular server is needed.

- Swagger: http://localhost:8000/api/docs/
- Django Templates UI: http://localhost:8000/
- Django admin: http://localhost:8000/admin/

Use a superuser to create sample customer accounts in Django admin only after registering the models, or run `seed_demo`. The seed command creates account records; set customer passwords with `python manage.py changepassword alice` and `... bob`. It does not credit a genuine ledger-backed initial balance. This fixture is for isolated testing only.

## Sample API

`POST /api/v1/auth/register/` with username, email, password; `POST /api/v1/auth/login/` to obtain JWT. `GET /api/v1/accounts/`, `GET /api/v1/transfers/` and `POST /api/v1/transfers/` require bearer token. Transfer requires `Idempotency-Key` header and JSON body:

```json
{"source":"<source-account-uuid>","destination":"<destination-account-uuid>","amount":"100.00"}
```

First successful transfer returns HTTP 201, replay returns 200. A rejected transfer is persisted with status `REJECTED` and HTTP 201 (created rejection resource). This is an internal simulated transfer, not an actual bank payment.

## Testing

```bash
pytest -q
python manage.py check
python manage.py check --deploy --settings=config.settings.production
```

Production settings deliberately require a real secret and explicit hosts. Run deploy checks with valid environment configuration. Run migrations before tests or API requests. The repository ships model source, not generated migration files; generate and review migrations before real deployment.

## Constraints

- Account creation and money issuance are intentionally not exposed as unrestricted customer APIs.
- Customer UI displays API data, not hardcoded balances.
- Outbox worker is a demonstration handler and must not be mistaken for actual delivery.
- Loans, cards, bills and investments expose limited **simulated** write workflows; see DELIVERY_STATUS.md for exact coverage and limitations.
- Compliance and high availability are documented work items, not achieved certifications.
