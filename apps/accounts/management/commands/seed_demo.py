from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Account
from decimal import Decimal
class Command(BaseCommand):
 help='Create isolated simulation accounts; never run against real funds'
 def handle(self,*args,**kwargs):
  User=get_user_model()
  for username,balance,number in [('alice',Decimal('25000.00'),'SIM0000000001'),('bob',Decimal('8000.00'),'SIM0000000002')]:
   user,_=User.objects.get_or_create(username=username,defaults={'email':f'{username}@example.test'})
   # No default credentials: use changepassword explicitly.
   Account.objects.get_or_create(number=number,defaults={'owner':user,'balance':balance})
  self.stdout.write(self.style.SUCCESS('Demo users alice/bob (set passwords manually via changepassword); accounts created'))
