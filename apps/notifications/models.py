from django.db import models
class OutboxEvent(models.Model):
 topic=models.CharField(max_length=100)
 payload=models.JSONField()
 delivered_at=models.DateTimeField(null=True,blank=True)
 attempts=models.PositiveIntegerField(default=0)
 created_at=models.DateTimeField(auto_now_add=True)
