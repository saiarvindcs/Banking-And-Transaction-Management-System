from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
 class Role(models.TextChoices):
  CUSTOMER='CUSTOMER';OPERATOR='OPERATOR';APPROVER='APPROVER';ADMIN='ADMIN'
 role=models.CharField(max_length=16,choices=Role.choices,default=Role.CUSTOMER)
 mfa_enabled=models.BooleanField(default=False)
 mfa_secret=models.CharField(max_length=64,blank=True)
