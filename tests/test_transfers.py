from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from apps.transfers.services import execute_transfer
from apps.ledger.models import LedgerEntry
@pytest.mark.django_db(transaction=True)
def test_transfer_idempotent_and_balanced():
 u=get_user_model().objects.create_user(username='test1',password='safe-test-pass')
 v=get_user_model().objects.create_user(username='test2',password='safe-test-pass')
 a=Account.objects.create(owner=u,number='TEST0001',balance=Decimal('100.00'))
 b=Account.objects.create(owner=v,number='TEST0002',balance=Decimal('0.00'))
 first,created=execute_transfer(user=u,source_id=a.pk,destination_id=b.pk,amount='30.00',key='key-1')
 second,reused=execute_transfer(user=u,source_id=a.pk,destination_id=b.pk,amount='30.00',key='key-1')
 a.refresh_from_db();b.refresh_from_db()
 assert created and not reused and first.pk==second.pk
 assert a.balance==Decimal('70.00') and b.balance==Decimal('30.00')
 assert LedgerEntry.objects.filter(journal=first.journal).count()==2
@pytest.mark.django_db(transaction=True)
def test_rejected_transfer_persists():
 u=get_user_model().objects.create_user(username='test3')
 a=Account.objects.create(owner=u,number='TEST0003',balance=Decimal('5'))
 b=Account.objects.create(owner=u,number='TEST0004',balance=Decimal('0'))
 transfer,_=execute_transfer(user=u,source_id=a.pk,destination_id=b.pk,amount='10',key='no-funds')
 assert transfer.status=='REJECTED' and transfer.failure_reason=='Insufficient funds'
