from decimal import Decimal
from rest_framework import serializers,status,viewsets,mixins,permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Transfer
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import F
from apps.accounts.models import Account
from apps.ledger.models import Journal, LedgerEntry
from apps.audit.models import AuditEvent
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .services import execute_transfer
class TransferSerializer(serializers.ModelSerializer):
 class Meta:
  model=Transfer;fields=['id','source','destination','amount','status','failure_reason','created_at'];read_only_fields=fields
class TransferCreateSerializer(serializers.Serializer):
 source=serializers.UUIDField();destination=serializers.UUIDField();amount=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal("0.01"))
class TransferViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.CreateModelMixin,viewsets.GenericViewSet):
 serializer_class=TransferSerializer
 filterset_fields=['status','source','destination'];ordering_fields=['created_at','amount'];search_fields=['idempotency_key']
 def get_queryset(self): return Transfer.objects.filter(initiated_by=self.request.user).select_related('source','destination')
 @extend_schema(request=TransferCreateSerializer,parameters=[OpenApiParameter(name='Idempotency-Key',type=str,location=OpenApiParameter.HEADER,required=True,description='Unique request key; reuse only for identical retries')],responses={201:TransferSerializer,200:TransferSerializer,400:OpenApiResponse(description='Validation or transfer rejection'),403:OpenApiResponse(description='Forbidden')})
 def create(self,request,*args,**kwargs):
  incoming=TransferCreateSerializer(data=request.data);incoming.is_valid(raise_exception=True)
  key=request.headers.get('Idempotency-Key')
  transfer,created=execute_transfer(user=request.user,key=key,**{'source_id':incoming.validated_data['source'],'destination_id':incoming.validated_data['destination'],'amount':incoming.validated_data['amount']})
  return Response(TransferSerializer(transfer).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

 @extend_schema(request=None,responses={201:dict,200:dict})
 @action(detail=True,methods=['post'],url_path='reverse')
 def reverse(self,request,pk=None):
  # Only staff may reverse completed transfers. The original journal is immutable.
  if not (request.user.is_superuser or getattr(request.user,'role',None) in ('OPERATOR','APPROVER','ADMIN')):
   from rest_framework.exceptions import PermissionDenied
   raise PermissionDenied('Staff access required')
  with transaction.atomic():
   try: transfer=Transfer.objects.select_for_update().get(pk=pk)
   except Transfer.DoesNotExist: raise ValidationError('Transfer not found')
   reference=f'REVERSAL:{transfer.pk}'
   previous=Journal.objects.filter(reference=reference).first()
   if previous: return Response({'reference':reference,'status':'ALREADY_REVERSED'},status=200)
   if transfer.status!='COMPLETED' or not transfer.journal_id: raise ValidationError('Only completed transfers can be reversed')
   accounts={str(a.pk):a for a in Account.objects.select_for_update().filter(pk__in=[transfer.source_id,transfer.destination_id]).order_by('pk')}
   source=accounts[str(transfer.source_id)];destination=accounts[str(transfer.destination_id)]
   if source.status!='ACTIVE' or destination.status!='ACTIVE': raise ValidationError('Both accounts must be active')
   if destination.balance<transfer.amount: raise ValidationError('Destination has insufficient funds for reversal')
   journal=Journal.objects.create(reference=reference)
   LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=destination,side='DEBIT',amount=transfer.amount),LedgerEntry(journal=journal,account=source,side='CREDIT',amount=transfer.amount)])
   Account.objects.filter(pk=destination.pk).update(balance=F('balance')-transfer.amount)
   Account.objects.filter(pk=source.pk).update(balance=F('balance')+transfer.amount)
   AuditEvent.objects.create(actor=request.user,action='TRANSFER_REVERSED',object_ref=str(transfer.pk),details={'reversal_reference':reference,'amount':str(transfer.amount)})
  return Response({'reference':reference,'status':'REVERSED','original_transfer':str(transfer.pk)},status=201)
