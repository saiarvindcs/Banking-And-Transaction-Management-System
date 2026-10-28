"""API regression tests for original features and new operations. Run with pytest -q."""
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import Account
from apps.ledger.models import Journal, LedgerEntry
from apps.transfers.models import Transfer
from apps.cards.models import Card

@pytest.fixture
def scenario(db):
    User=get_user_model()
    a=User.objects.create_user(username='release_a',password='GoodPassword123!')
    b=User.objects.create_user(username='release_b',password='GoodPassword123!')
    admin=User.objects.create_superuser(username='release_admin',email='admin@testing.invalid',password='GoodPassword123!')
    source=Account.objects.create(owner=a,number='RELEASE-A',balance=Decimal('0'))
    target=Account.objects.create(owner=b,number='RELEASE-B',balance=Decimal('0'))
    return a,b,admin,source,target

@pytest.mark.django_db(transaction=True)
def test_deposit_transfer_reversal_preserves_immutable_original(scenario):
    a,b,admin,source,target=scenario
    api=APIClient();api.force_authenticate(user=admin)
    funding={'account':str(source.pk),'amount':'200.00','reference':'RELEASE-DEP-001'}
    assert api.post('/api/v1/operations/deposits/',funding,format='json').status_code==201
    assert api.post('/api/v1/operations/deposits/',funding,format='json').status_code==200
    api.force_authenticate(user=a)
    transfer=api.post('/api/v1/transfers/',{'source':str(source.pk),'destination':str(target.pk),'amount':'75.00'},format='json',HTTP_IDEMPOTENCY_KEY='RELEASE-TRANSFER-001')
    assert transfer.status_code==201,transfer.data
    tid=transfer.data['id']
    assert api.post('/api/v1/transfers/',{'source':str(source.pk),'destination':str(target.pk),'amount':'75.00'},format='json',HTTP_IDEMPOTENCY_KEY='RELEASE-TRANSFER-001').status_code==200
    original=Transfer.objects.get(pk=tid);original_journal=original.journal_id
    api.force_authenticate(user=admin)
    reverse=api.post(f'/api/v1/transfers/{tid}/reverse/')
    assert reverse.status_code==201,reverse.data
    assert api.post(f'/api/v1/transfers/{tid}/reverse/').status_code==200
    source.refresh_from_db();target.refresh_from_db();original.refresh_from_db()
    assert source.balance==Decimal('200.00') and target.balance==Decimal('0.00')
    assert original.status=='COMPLETED' and original.journal_id==original_journal
    assert Journal.objects.filter(reference=f'REVERSAL:{tid}').count()==1
    assert LedgerEntry.objects.filter(journal_id=original_journal).count()==2
    assert api.get('/api/v1/operations/reconciliation/').data['count']==0

@pytest.mark.django_db(transaction=True)
def test_withdrawal_and_customer_permissions(scenario):
    a,b,admin,source,target=scenario
    api=APIClient();api.force_authenticate(user=admin)
    assert api.post('/api/v1/operations/deposits/',{'account':str(source.pk),'amount':'100','reference':'RELEASE-DEP-002'},format='json').status_code==201
    data={'account':str(source.pk),'amount':'40.00','reference':'RELEASE-WD-001'}
    assert api.post('/api/v1/operations/withdrawals/',data,format='json').status_code==201
    assert api.post('/api/v1/operations/withdrawals/',data,format='json').status_code==200
    source.refresh_from_db();assert source.balance==Decimal('60.00')
    api.force_authenticate(user=a)
    assert api.post('/api/v1/operations/withdrawals/',data,format='json').status_code==403
    assert api.get('/api/v1/operations/reconciliation/').status_code==403

@pytest.mark.django_db(transaction=True)
def test_card_cannot_be_unblocked_by_freeze_or_activate(scenario):
    a,b,admin,source,target=scenario
    card=Card.objects.create(account=source,token='release-token',last_four='2026',status='BLOCKED')
    api=APIClient();api.force_authenticate(user=a)
    assert api.post(f'/api/v1/cards/{card.pk}/activate/').status_code==400
    assert api.post(f'/api/v1/cards/{card.pk}/freeze/').status_code==400
    card.refresh_from_db();assert card.status=='BLOCKED'

@pytest.mark.django_db(transaction=True)
def test_bill_investment_and_account_statement(scenario):
    a,b,admin,source,target=scenario
    api=APIClient();api.force_authenticate(user=admin)
    assert api.post('/api/v1/operations/deposits/',{'account':str(source.pk),'amount':'1000','reference':'RELEASE-DEP-003'},format='json').status_code==201
    api.force_authenticate(user=a)
    bill={'account':str(source.pk),'biller':'Test Electricity','reference':'RELEASE-BILL-001','amount':'100.00'}
    assert api.post('/api/v1/bills/pay/',bill,format='json').status_code==201
    assert api.post('/api/v1/bills/pay/',bill,format='json').status_code==200
    buy={'account':str(source.pk),'symbol':'TCS','quantity':'2','simulated_unit_price':'100.00'}
    assert api.post('/api/v1/investments/buy/',buy,format='json').status_code==201
    sell={**buy,'quantity':'1','simulated_unit_price':'110.00'}
    assert api.post('/api/v1/investments/sell/',sell,format='json').status_code==201
    source.refresh_from_db();assert source.balance==Decimal('810.00')
    assert api.get('/api/v1/accounts/').status_code==200
    assert api.get(f'/api/v1/accounts/{source.pk}/statement/').status_code==200
    assert api.get('/api/v1/bills/').status_code==200
    assert api.get('/api/v1/investments/').status_code==200
