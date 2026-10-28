# Testing the Django Templates edition

1. Extract into a NEW folder; do not overwrite the currently running project or its database volume.
2. Copy `.env.example` to `.env` and configure unique development credentials.
3. `docker compose up -d --build`
4. `docker compose exec api python manage.py check`
5. `docker compose exec api python manage.py makemigrations`
6. **Review generated migrations**, then `docker compose exec api python manage.py migrate`.
7. Open `http://localhost:8000/` for Django Templates login and registration.
8. Open `http://localhost:8000/api/docs/` for Swagger.
9. API endpoints added: `/api/v1/accounts/{uuid}/statement/`, `/api/v1/operations/audit/`, `/api/v1/operations/risk/`.
10. For a privileged admin in a local simulation: `docker compose exec api python manage.py createsuperuser`.

## Limits
This is a development candidate, not a fully implemented seven-phase banking product. Account provisioning, cash settlement, loan servicing, card settlement, bill payment execution, investment order execution, MFA enforcement, disaster recovery automation, and complete integration testing remain outstanding. Do not use real money or customer data.
