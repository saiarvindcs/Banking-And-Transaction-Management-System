import secrets
from decimal import Decimal
from rest_framework import serializers,viewsets,status
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.accounts.models import Account
from apps.audit.models import AuditEvent
from .models import Card
from django.db import transaction
class CardSerializer(serializers.ModelSerializer):
 class Meta:
  model=Card;fields=['id','account','last_four','status','daily_limit'];read_only_fields=fields
class IssueCardSerializer(serializers.Serializer):
 account=serializers.UUIDField()
 daily_limit=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('1'),required=False,default=Decimal('10000'))
class CardViewSet(viewsets.ReadOnlyModelViewSet):
 serializer_class=CardSerializer
 def get_queryset(self): return Card.objects.filter(account__owner=self.request.user)
 @extend_schema(request=IssueCardSerializer,responses={201:CardSerializer})
 @action(detail=False,methods=['post'],url_path='issue')
 def issue(self,request):
  data=IssueCardSerializer(data=request.data);data.is_valid(raise_exception=True)
  try: account=Account.objects.get(pk=data.validated_data['account'],owner=request.user,status='ACTIVE')
  except Account.DoesNotExist: raise ValidationError({'account':'Active account not found'})
  card=Card.objects.create(account=account,token=secrets.token_urlsafe(40),last_four=f'{secrets.randbelow(10000):04d}',status='ACTIVE',daily_limit=data.validated_data['daily_limit'])
  AuditEvent.objects.create(actor=request.user,action='CARD_ISSUED',object_ref=str(card.pk),details={})
  return Response(CardSerializer(card).data,status=201)
 @extend_schema(request=None,responses={200:CardSerializer})
 @action(detail=True,methods=['post'])
 def freeze(self,request,pk=None):
  card=self.get_object()
  if card.status=='BLOCKED': raise ValidationError('Blocked card cannot be frozen')
  card.status='FROZEN';card.save(update_fields=['status']);AuditEvent.objects.create(actor=request.user,action='CARD_FROZEN',object_ref=str(card.pk),details={});return Response(CardSerializer(card).data)
 @extend_schema(request=None,responses={200:CardSerializer})
 @action(detail=True,methods=['post'])
 def activate(self,request,pk=None):
  with transaction.atomic():
   card=Card.objects.select_for_update().get(pk=self.get_object().pk)
   if card.status=='BLOCKED': raise ValidationError('Blocked card cannot be reactivated')
   card.status='ACTIVE';card.save(update_fields=['status'])
  return Response(CardSerializer(card).data)
 @extend_schema(request=None,responses={200:CardSerializer})
 @action(detail=True,methods=['post'])
 def block(self,request,pk=None):
  card=self.get_object()
  if card.status=='BLOCKED': raise ValidationError('Card already blocked')
  card.status='BLOCKED';card.save(update_fields=['status']);AuditEvent.objects.create(actor=request.user,action='CARD_BLOCKED',object_ref=str(card.pk),details={});return Response(CardSerializer(card).data)
