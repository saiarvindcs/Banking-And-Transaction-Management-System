from django.db import models
class RiskAlert(models.Model):
 transfer=models.ForeignKey('transfers.Transfer',on_delete=models.CASCADE)
 rule=models.CharField(max_length=100)
 score=models.PositiveIntegerField(default=0)
 resolved=models.BooleanField(default=False)
 created_at=models.DateTimeField(auto_now_add=True)
