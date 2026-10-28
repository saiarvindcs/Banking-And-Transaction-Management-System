from django.conf import settings
from django.db import models
class Holding(models.Model):
 owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
 symbol=models.CharField(max_length=20)
 quantity=models.DecimalField(max_digits=19,decimal_places=6)
 cost_basis=models.DecimalField(max_digits=19,decimal_places=2)
 class Meta: constraints=[models.UniqueConstraint(fields=['owner','symbol'],name='unique_holding_symbol')]
