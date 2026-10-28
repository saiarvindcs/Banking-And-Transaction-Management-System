import uuid
from django.db import models
class Journal(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
 reference=models.CharField(max_length=100,unique=True)
 created_at=models.DateTimeField(auto_now_add=True)
 class Meta: ordering=['-created_at']
class LedgerEntry(models.Model):
 class Side(models.TextChoices): DEBIT='DEBIT';CREDIT='CREDIT'
 journal=models.ForeignKey(Journal,on_delete=models.PROTECT,related_name='entries')
 account=models.ForeignKey('accounts.Account',on_delete=models.PROTECT)
 side=models.CharField(max_length=6,choices=Side.choices)
 amount=models.DecimalField(max_digits=19,decimal_places=2)
 created_at=models.DateTimeField(auto_now_add=True)
 class Meta:
  constraints=[models.CheckConstraint(condition=models.Q(amount__gt=0),name='positive_ledger_entry')]
