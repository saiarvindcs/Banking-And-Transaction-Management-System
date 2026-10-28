from django.db import models
class BillPayment(models.Model):
 account=models.ForeignKey('accounts.Account',on_delete=models.PROTECT)
 biller=models.CharField(max_length=100)
 reference=models.CharField(max_length=100,unique=True)
 amount=models.DecimalField(max_digits=19,decimal_places=2)
 status=models.CharField(max_length=20,default='PENDING')
