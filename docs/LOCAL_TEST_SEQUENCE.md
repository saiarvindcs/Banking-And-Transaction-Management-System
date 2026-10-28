# Local test sequence

1. Copy `.env.example` to `.env`, set unique local secrets and PostgreSQL password.
2. `docker compose up -d --build`
3. `docker compose exec api python manage.py check`
4. `docker compose exec api python manage.py makemigrations`
5. `docker compose exec api python manage.py migrate`
6. Open `http://localhost:8000/register/` and create a test user.
7. Open `http://localhost:8000/` and create an account. It starts with zero funds.
8. Create a second test user and account; transfer testing requires a controlled simulation funding source. Do not directly edit balances in production.
9. Open `http://localhost:8000/api/docs/` to inspect API contracts and test JWT endpoints.
10. `docker compose exec api pytest -q` to run available tests.

No production claim is made until integration, concurrency, restore and security tests have passed.
