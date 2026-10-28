"""Regression checks for reported failures and new banking operations."""
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import Account
from apps.cards.models import Card
from apps.ledger.models import Journal, LedgerEntry
from apps.loans.models import LoanPayment
from apps.notifications.models import OutboxEvent

@pytest.fixture
def setup_users(db):
    User = get_user_model()
    customer = User.objects.create_user(username='regression_customer', password='VeryStrongPass!42')
    admin = User.objects.create_superuser(username='regression_admin', email='admin@example.test', password='VeryStrongPass!42')
    account = Account.objects.create(owner=customer, number='REGRESSION-ACCOUNT', balance=Decimal('500.00'))
    return customer, admin, account

@pytest.mark.django_db(transaction=True)
def test_reconciliation_and_withdrawal_idempotency(setup_users):
    customer, admin, account = setup_users
    api = APIClient(); api.force_authenticate(user=admin)
    data = {'account':str(account.pk), 'amount':'50.00', 'reference':'REGRESSION-WITHDRAW-01'}
    first = api.post('/api/v1/operations/withdrawals/', data, format='json')
    assert first.status_code == 201, first.data
    second = api.post('/api/v1/operations/withdrawals/', data, format='json')
    assert second.status_code == 200, second.data
    account.refresh_from_db()
    assert account.balance == Decimal('450.00')
    assert Journal.objects.filter(reference='WITHDRAWAL:REGRESSION-WITHDRAW-01').count() == 1
    response = api.get('/api/v1/operations/reconciliation/')
    assert response.status_code == 200
    assert response.data['count'] == 0

@pytest.mark.django_db(transaction=True)
def test_customer_cannot_withdraw(setup_users):
    customer, admin, account = setup_users
    api = APIClient(); api.force_authenticate(user=customer)
    response = api.post('/api/v1/operations/withdrawals/', {'account':str(account.pk),'amount':'10','reference':'REGRESSION-DENIED'}, format='json')
    assert response.status_code == 403

@pytest.mark.django_db(transaction=True)
def test_blocked_card_never_reactivates(setup_users):
    customer, admin, account = setup_users
    card = Card.objects.create(account=account, token='regression-token', last_four='1234', status='BLOCKED', daily_limit=Decimal('10000'))
    api = APIClient(); api.force_authenticate(user=customer)
    response = api.post(f'/api/v1/cards/{card.pk}/activate/')
    assert response.status_code == 400
    card.refresh_from_db()
    assert card.status == 'BLOCKED'

@pytest.mark.django_db(transaction=True)
def test_weak_password_rejected(db):
    api = APIClient()
    response = api.post('/api/v1/auth/register/', {'username':'weak_regression','password':'123'}, format='json')
    assert response.status_code == 400

@pytest.mark.django_db(transaction=True)
def test_loanpayment_table_exists(db):
    from django.db import connection
    assert LoanPayment._meta.db_table in connection.introspection.table_names()

@pytest.mark.django_db(transaction=True)
def test_notifications_are_private(setup_users):
    customer, admin, account = setup_users
    event = OutboxEvent.objects.create(topic='IN_APP_NOTIFICATION',payload={'user_id':customer.pk,'action':'CARD_BLOCKED'})
    api = APIClient();api.force_authenticate(user=customer)
    result = api.get('/api/v1/notifications/')
    assert result.status_code == 200
    assert any(row['id'] == event.pk for row in result.data['results'])
    api.force_authenticate(user=admin)
    other = api.get('/api/v1/notifications/')
    assert all(row['id'] != event.pk for row in other.data['results'])
