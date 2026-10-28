from django.conf import settings
from django.db import models
class Loan(models.Model):
 owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
 principal=models.DecimalField(max_digits=19,decimal_places=2)
 annual_rate=models.DecimalField(max_digits=6,decimal_places=3)
 term_months=models.PositiveIntegerField()
 status=models.CharField(max_length=20,default='APPLICATION')
 created_at=models.DateTimeField(auto_now_add=True)

class LoanPayment(models.Model):
 loan=models.ForeignKey(Loan,on_delete=models.PROTECT,related_name='payments')
 account=models.ForeignKey('accounts.Account',on_delete=models.PROTECT)
 amount=models.DecimalField(max_digits=19,decimal_places=2)
 reference=models.CharField(max_length=100,unique=True)
 created_at=models.DateTimeField(auto_now_add=True)
