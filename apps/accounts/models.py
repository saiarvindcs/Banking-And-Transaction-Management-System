import uuid
from django.conf import settings
from django.db import models
class Account(models.Model):
 class Status(models.TextChoices):
  ACTIVE='ACTIVE';FROZEN='FROZEN';CLOSED='CLOSED'
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='bank_accounts')
 number=models.CharField(max_length=24,unique=True)
 currency=models.CharField(max_length=3,default='INR')
 balance=models.DecimalField(max_digits=19,decimal_places=2,default=0)
 status=models.CharField(max_length=10,choices=Status.choices,default=Status.ACTIVE)
 daily_limit=models.DecimalField(max_digits=19,decimal_places=2,default=100000)
 created_at=models.DateTimeField(auto_now_add=True)
 class Meta:
  constraints=[models.CheckConstraint(condition=models.Q(balance__gte=0),name='nonnegative_account_balance')]
class Beneficiary(models.Model):
 owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
 account=models.ForeignKey(Account,on_delete=models.CASCADE)
 nickname=models.CharField(max_length=80)
 verified=models.BooleanField(default=False)
 created_at=models.DateTimeField(auto_now_add=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['owner','account'],name='unique_beneficiary')]
