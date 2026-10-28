from django.db import models
class Card(models.Model):
 account=models.ForeignKey('accounts.Account',on_delete=models.PROTECT)
 token=models.CharField(max_length=80,unique=True)
 last_four=models.CharField(max_length=4)
 status=models.CharField(max_length=20,default='ACTIVE')
 daily_limit=models.DecimalField(max_digits=19,decimal_places=2,default=10000)
class CardAuthorization(models.Model):
 card=models.ForeignKey(Card,on_delete=models.PROTECT)
 amount=models.DecimalField(max_digits=19,decimal_places=2)
 status=models.CharField(max_length=20,default='HELD')
 created_at=models.DateTimeField(auto_now_add=True)
