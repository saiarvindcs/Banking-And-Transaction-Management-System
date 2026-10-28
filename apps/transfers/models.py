import uuid
from django.conf import settings
from django.db import models
class Transfer(models.Model):
 class Status(models.TextChoices):
  PENDING='PENDING';COMPLETED='COMPLETED';REJECTED='REJECTED'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 initiated_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
 source=models.ForeignKey('accounts.Account',on_delete=models.PROTECT,related_name='outgoing')
 destination=models.ForeignKey('accounts.Account',on_delete=models.PROTECT,related_name='incoming')
 amount=models.DecimalField(max_digits=19,decimal_places=2)
 idempotency_key=models.CharField(max_length=128)
 status=models.CharField(max_length=12,choices=Status.choices,default=Status.PENDING)
 failure_reason=models.CharField(max_length=255,blank=True)
 journal=models.OneToOneField('ledger.Journal',null=True,blank=True,on_delete=models.PROTECT)
 created_at=models.DateTimeField(auto_now_add=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['initiated_by','idempotency_key'],name='unique_transfer_idempotency'),models.CheckConstraint(condition=models.Q(amount__gt=0),name='positive_transfer_amount')]
