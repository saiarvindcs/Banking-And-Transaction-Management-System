from decimal import Decimal
from django import forms
from apps.accounts.models import Account

class TransferForm(forms.Form):
    source = forms.ModelChoiceField(queryset=Account.objects.none())
    destination = forms.ModelChoiceField(queryset=Account.objects.none())
    amount = forms.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'))
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['source'].queryset=Account.objects.filter(owner=user,status='ACTIVE')
        self.fields['destination'].queryset=Account.objects.filter(status='ACTIVE').exclude(owner=user)
