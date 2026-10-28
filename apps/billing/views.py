from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.accounts.models import Account
from apps.accounts.clearing import clearing_account
from apps.ledger.models import Journal,LedgerEntry
from apps.audit.models import AuditEvent
from .models import BillPayment
class BillSerializer(serializers.ModelSerializer):
 class Meta:
  model=BillPayment;fields=['id','account','biller','reference','amount','status'];read_only_fields=fields
class BillPayInput(serializers.Serializer):
 account=serializers.UUIDField()
 biller=serializers.CharField(max_length=100)
 reference=serializers.RegexField(regex=r'^[A-Za-z0-9_-]{8,80}$',max_length=80)
 amount=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'))
class BillViewSet(viewsets.ReadOnlyModelViewSet):
 serializer_class=BillSerializer
 def get_queryset(self):return BillPayment.objects.filter(account__owner=self.request.user).order_by("id")
 @extend_schema(request=BillPayInput,responses={201:BillSerializer,200:BillSerializer})
 @action(detail=False,methods=['post'],url_path='pay')
 def pay(self,request):
  data=BillPayInput(data=request.data);data.is_valid(raise_exception=True);v=data.validated_data
  with transaction.atomic():
   from apps.identity.models import User
   User.objects.select_for_update().get(pk=request.user.pk)
   existing=BillPayment.objects.filter(reference=v['reference']).first()
   if existing:
    if existing.account.owner_id!=request.user.pk or existing.account_id!=v['account'] or existing.amount!=v['amount'] or existing.biller!=v['biller']:raise ValidationError('Reference already used')
    return Response(BillSerializer(existing).data,status=200)
   try: account=Account.objects.select_for_update().get(pk=v['account'],owner=request.user,status='ACTIVE')
   except Account.DoesNotExist:raise ValidationError('Account not found')
   if account.balance<v['amount']:raise ValidationError('Insufficient funds')
   payment=BillPayment.objects.create(account=account,biller=v['biller'],reference=v['reference'],amount=v['amount'],status='SIMULATED')
   Account.objects.filter(pk=account.pk,balance__gte=v['amount']).update(balance=F('balance')-v['amount'])
   journal=Journal.objects.create(reference='BILL:'+v['reference'])
   # Offset is a simulated payable, represented by the system clearing account.
   clearing=clearing_account()
   LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=account,side='DEBIT',amount=v['amount']),LedgerEntry(journal=journal,account=clearing,side='CREDIT',amount=v['amount'])])
   AuditEvent.objects.create(actor=request.user,action='SIMULATED_BILL_PAYMENT',object_ref=str(payment.pk),details={'reference':v['reference']})
  return Response(BillSerializer(payment).data,status=201)
