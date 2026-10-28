from decimal import Decimal
from apps.accounts.models import Account
from apps.identity.models import User

def clearing_account():
    owner,_=User.objects.get_or_create(username='__system_clearing__',defaults={'is_active':False,'role':'ADMIN'})
    account,_=Account.objects.get_or_create(number='SYSTEM-CLEARING-INR',defaults={'owner':owner,'currency':'INR','balance':Decimal('0.00'),'status':'ACTIVE'})
    return account
