from django.conf import settings
from django.db import models
class AuditEvent(models.Model):
 actor=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
 action=models.CharField(max_length=100)
 object_ref=models.CharField(max_length=100)
 details=models.JSONField(default=dict)
 created_at=models.DateTimeField(auto_now_add=True)
