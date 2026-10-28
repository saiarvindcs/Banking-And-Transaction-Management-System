
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import Account
from apps.transfers.services import execute_transfer
from apps.ledger.models import LedgerEntry


@pytest.mark.django_db(transaction=True)
def test_transfer_idempotent_and_balanced():
    User = get_user_model()

    u = User.objects.create_user(
        username='test1',
        password='safe-test-pass'
    )

    v = User.objects.create_user(
        username='test2',
        password='safe-test-pass'
    )

    a = Account.objects.create(
        owner=u,
        number='TEST0001',
        balance=Decimal('100.00')
    )

    b = Account.objects.create(
        owner=v,
        number='TEST0002',
        balance=Decimal('0.00')
    )

    # The destination account must be a verified beneficiary.
    # Use the existing Beneficiary model from the accounts app.
    from apps.accounts.models import Beneficiary

    Beneficiary.objects.create(
        owner=u,
        account=b,
        verified=True
    )

    first, created = execute_transfer(
        user=u,
        source_id=a.pk,
        destination_id=b.pk,
        amount='30.00',
        key='key-1'
    )

    second, reused = execute_transfer(
        user=u,
        source_id=a.pk,
        destination_id=b.pk,
        amount='30.00',
        key='key-1'
    )

    a.refresh_from_db()
    b.refresh_from_db()

    assert created
    assert not reused
    assert first.pk == second.pk

    assert a.balance == Decimal('70.00')
    assert b.balance == Decimal('30.00')

    assert LedgerEntry.objects.filter(
        journal=first.journal
    ).count() == 2


@pytest.mark.django_db(transaction=True)
def test_rejected_transfer_persists():
    User = get_user_model()

    u = User.objects.create_user(
        username='test3'
    )

    a = Account.objects.create(
        owner=u,
        number='TEST0003',
        balance=Decimal('5.00')
    )

    b = Account.objects.create(
        owner=u,
        number='TEST0004',
        balance=Decimal('0.00')
    )

    transfer, _ = execute_transfer(
        user=u,
        source_id=a.pk,
        destination_id=b.pk,
        amount='10.00',
        key='no-funds'
    )

    assert transfer.status == 'REJECTED'
    assert transfer.failure_reason == 'Insufficient funds'
