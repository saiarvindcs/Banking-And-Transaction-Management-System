
"""API regression tests for original features and new banking operations."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Account
from apps.accounts.models import Account, Beneficiary
from apps.ledger.models import Journal, LedgerEntry
from apps.transfers.models import Transfer
from apps.cards.models import Card


@pytest.fixture
def scenario(db):
    User = get_user_model()

    a = User.objects.create_user(
        username='release_a',
        password='GoodPassword123!'
    )

    b = User.objects.create_user(
        username='release_b',
        password='GoodPassword123!'
    )

    admin = User.objects.create_superuser(
        username='release_admin',
        email='admin@testing.invalid',
        password='GoodPassword123!'
    )

    source = Account.objects.create(
        owner=a,
        number='RELEASE-A',
        balance=Decimal('0.00')
    )

    target = Account.objects.create(
        owner=b,
        number='RELEASE-B',
        balance=Decimal('0.00')
    )

    return a, b, admin, source, target


@pytest.mark.django_db(transaction=True)
def test_deposit_transfer_reversal_preserves_immutable_original(scenario):
    a, b, admin, source, target = scenario

    api = APIClient()
    api.force_authenticate(user=admin)

    funding = {
        'account': str(source.pk),
        'amount': '200.00',
        'reference': 'RELEASE-DEP-001'
    }

    first_deposit = api.post(
        '/api/v1/operations/deposits/',
        funding,
        format='json'
    )
    assert first_deposit.status_code == 201, first_deposit.data

    repeated_deposit = api.post(
        '/api/v1/operations/deposits/',
        funding,
        format='json'
    )
    assert repeated_deposit.status_code == 200, repeated_deposit.data

    # The destination must be a verified beneficiary.
    Beneficiary.objects.create(
        owner=a,
        account=target,
        verified=True
    )

    api.force_authenticate(user=a)

    transfer_data = {
        'source': str(source.pk),
        'destination': str(target.pk),
        'amount': '75.00'
    }

    transfer = api.post(
        '/api/v1/transfers/',
        transfer_data,
        format='json',
        HTTP_IDEMPOTENCY_KEY='RELEASE-TRANSFER-001'
    )

    assert transfer.status_code == 201, transfer.data

    transfer_id = transfer.data['id']

    repeated_transfer = api.post(
        '/api/v1/transfers/',
        transfer_data,
        format='json',
        HTTP_IDEMPOTENCY_KEY='RELEASE-TRANSFER-001'
    )

    assert repeated_transfer.status_code == 200, repeated_transfer.data

    original = Transfer.objects.get(pk=transfer_id)
    original_journal = original.journal_id

    api.force_authenticate(user=admin)

    reverse = api.post(
        f'/api/v1/transfers/{transfer_id}/reverse/'
    )
    assert reverse.status_code == 201, reverse.data

    repeated_reverse = api.post(
        f'/api/v1/transfers/{transfer_id}/reverse/'
    )
    assert repeated_reverse.status_code == 200, repeated_reverse.data

    source.refresh_from_db()
    target.refresh_from_db()
    original.refresh_from_db()

    assert source.balance == Decimal('200.00')
    assert target.balance == Decimal('0.00')

    assert original.status == 'COMPLETED'
    assert original.journal_id == original_journal

    assert Journal.objects.filter(
        reference=f'REVERSAL:{transfer_id}'
    ).count() == 1

    assert LedgerEntry.objects.filter(
        journal_id=original_journal
    ).count() == 2

    reconciliation = api.get(
        '/api/v1/operations/reconciliation/'
    )

    assert reconciliation.status_code == 200
    assert reconciliation.data['count'] == 0


@pytest.mark.django_db(transaction=True)
def test_withdrawal_and_customer_permissions(scenario):
    a, b, admin, source, target = scenario

    api = APIClient()
    api.force_authenticate(user=admin)

    deposit = api.post(
        '/api/v1/operations/deposits/',
        {
            'account': str(source.pk),
            'amount': '100.00',
            'reference': 'RELEASE-DEP-002'
        },
        format='json'
    )

    assert deposit.status_code == 201, deposit.data

    data = {
        'account': str(source.pk),
        'amount': '40.00',
        'reference': 'RELEASE-WD-001'
    }

    first = api.post(
        '/api/v1/operations/withdrawals/',
        data,
        format='json'
    )
    assert first.status_code == 201, first.data

    repeated = api.post(
        '/api/v1/operations/withdrawals/',
        data,
        format='json'
    )
    assert repeated.status_code == 200, repeated.data

    source.refresh_from_db()
    assert source.balance == Decimal('60.00')

    # Customer can withdraw from their own account.
    api.force_authenticate(user=a)

    own_withdrawal = api.post(
        '/api/v1/operations/withdrawals/',
        {
            'account': str(source.pk),
            'amount': '10.00',
            'reference': 'RELEASE-CUSTOMER-WD-001'
        },
        format='json'
    )

    assert own_withdrawal.status_code == 201, own_withdrawal.data

    source.refresh_from_db()
    assert source.balance == Decimal('50.00')

    # Customer cannot withdraw from another user's account.
    unauthorized = api.post(
        '/api/v1/operations/withdrawals/',
        {
            'account': str(target.pk),
            'amount': '10.00',
            'reference': 'RELEASE-UNAUTHORIZED-WD-001'
        },
        format='json'
    )

    assert unauthorized.status_code == 403, unauthorized.data

    target.refresh_from_db()
    assert target.balance == Decimal('0.00')

    # Reconciliation remains restricted to staff.
    reconciliation = api.get(
        '/api/v1/operations/reconciliation/'
    )

    assert reconciliation.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_card_cannot_be_unblocked_by_freeze_or_activate(scenario):
    a, b, admin, source, target = scenario

    card = Card.objects.create(
        account=source,
        token='release-token',
        last_four='2026',
        status='BLOCKED'
    )

    api = APIClient()
    api.force_authenticate(user=a)

    activate = api.post(
        f'/api/v1/cards/{card.pk}/activate/'
    )
    assert activate.status_code == 400

    freeze = api.post(
        f'/api/v1/cards/{card.pk}/freeze/'
    )
    assert freeze.status_code == 400

    card.refresh_from_db()
    assert card.status == 'BLOCKED'


@pytest.mark.django_db(transaction=True)
def test_bill_investment_and_account_statement(scenario):
    a, b, admin, source, target = scenario

    api = APIClient()
    api.force_authenticate(user=admin)

    deposit = api.post(
        '/api/v1/operations/deposits/',
        {
            'account': str(source.pk),
            'amount': '1000.00',
            'reference': 'RELEASE-DEP-003'
        },
        format='json'
    )

    assert deposit.status_code == 201, deposit.data

    api.force_authenticate(user=a)

    bill = {
        'account': str(source.pk),
        'biller': 'Test Electricity',
        'reference': 'RELEASE-BILL-001',
        'amount': '100.00'
    }

    first_bill = api.post(
        '/api/v1/bills/pay/',
        bill,
        format='json'
    )
    assert first_bill.status_code == 201, first_bill.data

    repeated_bill = api.post(
        '/api/v1/bills/pay/',
        bill,
        format='json'
    )
    assert repeated_bill.status_code == 200, repeated_bill.data

    buy = {
        'account': str(source.pk),
        'symbol': 'TCS',
        'quantity': '2',
        'simulated_unit_price': '100.00'
    }

    purchase = api.post(
        '/api/v1/investments/buy/',
        buy,
        format='json'
    )
    assert purchase.status_code == 201, purchase.data

    sell = {
        **buy,
        'quantity': '1',
        'simulated_unit_price': '110.00'
    }

    sale = api.post(
        '/api/v1/investments/sell/',
        sell,
        format='json'
    )
    assert sale.status_code == 201, sale.data

    source.refresh_from_db()
    assert source.balance == Decimal('810.00')

    assert api.get('/api/v1/accounts/').status_code == 200

    statement = api.get(
        f'/api/v1/accounts/{source.pk}/statement/'
    )
    assert statement.status_code == 200

    assert api.get('/api/v1/bills/').status_code == 200
    assert api.get('/api/v1/investments/').status_code == 200
