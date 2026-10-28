from django.db import models
class ReconciliationRun(models.Model):
 started_at=models.DateTimeField(auto_now_add=True)
 completed_at=models.DateTimeField(null=True)
 mismatches=models.JSONField(default=list)
 status=models.CharField(max_length=20,default='RUNNING')
