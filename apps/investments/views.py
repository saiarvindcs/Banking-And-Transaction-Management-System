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
from .models import Holding
import uuid
class InvestmentSerializer(serializers.ModelSerializer):
 class Meta:
  model=Holding;fields=['id','symbol','quantity','cost_basis'];read_only_fields=fields
class TradeInput(serializers.Serializer):
 account=serializers.UUIDField()
 symbol=serializers.RegexField(regex=r'^[A-Z0-9.]{1,20}$',max_length=20)
 quantity=serializers.DecimalField(max_digits=19,decimal_places=6,min_value=Decimal('0.000001'))
 simulated_unit_price=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'))
class InvestmentViewSet(viewsets.ReadOnlyModelViewSet):
 serializer_class=InvestmentSerializer
 def get_queryset(self):return Holding.objects.filter(owner=self.request.user).order_by("id")
 def _trade(self,request,side):
  data=TradeInput(data=request.data);data.is_valid(raise_exception=True);v=data.validated_data
  amount=(v['quantity']*v['simulated_unit_price']).quantize(Decimal('0.01'))
  if amount<=0:raise ValidationError('Trade amount too small')
  with transaction.atomic():
   try:account=Account.objects.select_for_update().get(pk=v['account'],owner=request.user,status='ACTIVE')
   except Account.DoesNotExist:raise ValidationError('Account not found')
   holding=Holding.objects.select_for_update().filter(owner=request.user,symbol=v['symbol']).first()
   if side=='BUY':
    if account.balance<amount:raise ValidationError('Insufficient funds')
    if not holding:holding=Holding.objects.create(owner=request.user,symbol=v['symbol'],quantity=0,cost_basis=0)
    holding.quantity+=v['quantity'];holding.cost_basis+=amount
    Account.objects.filter(pk=account.pk).update(balance=F('balance')-amount)
   else:
    if not holding or holding.quantity<v['quantity']:raise ValidationError('Insufficient holdings')
    basis=(holding.cost_basis*v['quantity']/holding.quantity).quantize(Decimal('0.01'))
    holding.quantity-=v['quantity'];holding.cost_basis-=basis
    Account.objects.filter(pk=account.pk).update(balance=F('balance')+amount)
   holding.save()
   clearing=clearing_account()
   journal=Journal.objects.create(reference='PAPER_TRADE:'+str(uuid.uuid4()))
   debit,credit=(account,clearing) if side=='BUY' else (clearing,account)
   LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=debit,side='DEBIT',amount=amount),LedgerEntry(journal=journal,account=credit,side='CREDIT',amount=amount)])
   AuditEvent.objects.create(actor=request.user,action='PAPER_TRADE_'+side,object_ref=str(holding.pk),details={'amount':str(amount),'symbol':v['symbol']})
  return Response({'holding':InvestmentSerializer(holding).data,'trade_amount':str(amount),'simulation':True},status=201)
 @extend_schema(request=TradeInput,responses={201:dict})
 @action(detail=False,methods=['post'])
 def buy(self,request):return self._trade(request,'BUY')
 @extend_schema(request=TradeInput,responses={201:dict})
 @action(detail=False,methods=['post'])
 def sell(self,request):return self._trade(request,'SELL')
