from decimal import Decimal
from django.db import transaction,IntegrityError
from django.db.models import F,Sum
from rest_framework.exceptions import ValidationError,PermissionDenied
from apps.accounts.models import Account, Beneficiary
from apps.ledger.models import Journal,LedgerEntry
from apps.transfers.models import Transfer
from apps.audit.models import AuditEvent
from apps.notifications.models import OutboxEvent
from apps.risk.models import RiskAlert

def execute_transfer(*,user,source_id,destination_id,amount,key):
 amount=Decimal(str(amount))
 if not amount.is_finite() or amount<=0 or amount.as_tuple().exponent < -2: raise ValidationError('Invalid transfer amount')
 if str(source_id)==str(destination_id): raise ValidationError('Accounts must differ')
 if not key or len(key)>128: raise ValidationError('Valid Idempotency-Key required')
 with transaction.atomic():
  # Lock user row to serialize same-customer requests and make idempotency race-safe.
  from apps.identity.models import User
  User.objects.select_for_update().get(pk=user.pk)
  prior=Transfer.objects.filter(initiated_by=user,idempotency_key=key).first()
  if prior:
   if str(prior.source_id)!=str(source_id) or str(prior.destination_id)!=str(destination_id) or prior.amount!=amount: raise ValidationError('Idempotency key reused with different payload')
   return prior,False
  # Canonical lock order prevents opposite-direction transfer deadlocks.
  locked=list(Account.objects.select_for_update().filter(pk__in=[source_id,destination_id]).order_by('pk'))
  if len(locked)!=2: raise ValidationError('Account not found')
  by_id={str(a.pk):a for a in locked}
  source=by_id[str(source_id)];destination=by_id[str(destination_id)]
  if source.owner_id!=user.pk: raise PermissionDenied('Not your source account')
  if destination.number=='SYSTEM-CLEARING-INR': raise ValidationError('Invalid destination')
  if source.currency!=destination.currency: raise ValidationError('Currency mismatch')
  if source.owner_id!=destination.owner_id and not Beneficiary.objects.filter(owner=user,account=destination,verified=True).exists(): raise ValidationError('Destination must be a verified beneficiary')
  if source.status!='ACTIVE' or destination.status!='ACTIVE': raise ValidationError('Account inactive')
  transfer=Transfer.objects.create(initiated_by=user,source=source,destination=destination,amount=amount,idempotency_key=key)
  reason=None
  if amount>source.daily_limit: reason='Per-transfer limit exceeded'
  elif source.balance<amount: reason='Insufficient funds'
  else:
   from django.utils import timezone
   today=timezone.now().date()
   spent=Transfer.objects.filter(source=source,status='COMPLETED',created_at__date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
   if spent+amount>source.daily_limit: reason='Daily transfer limit exceeded'
  if reason:
   transfer.status='REJECTED';transfer.failure_reason=reason;transfer.save(update_fields=['status','failure_reason'])
   AuditEvent.objects.create(actor=user,action='TRANSFER_REJECTED',object_ref=str(transfer.pk),details={'reason':reason})
   return transfer,True
  # Both account balances are locked and guarded with DB expressions.
  changed=Account.objects.filter(pk=source.pk,balance__gte=amount).update(balance=F('balance')-amount)
  if changed!=1: raise ValidationError('Insufficient funds')
  Account.objects.filter(pk=destination.pk).update(balance=F('balance')+amount)
  journal=Journal.objects.create(reference=f'TRANSFER:{transfer.pk}')
  # Convention: debit = source decrease; credit = destination increase.
  LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=source,side='DEBIT',amount=amount),LedgerEntry(journal=journal,account=destination,side='CREDIT',amount=amount)])
  transfer.journal=journal;transfer.status='COMPLETED';transfer.save(update_fields=['journal','status'])
  if amount>=Decimal('50000'):
   RiskAlert.objects.create(transfer=transfer,rule='HIGH_VALUE_TRANSFER',score=50)
  AuditEvent.objects.create(actor=user,action='TRANSFER_COMPLETED',object_ref=str(transfer.pk),details={'amount':str(amount),'currency':source.currency})
  OutboxEvent.objects.create(topic='transfer.completed',payload={'transfer_id':str(transfer.pk),'user_id':user.pk})
  return transfer,True
