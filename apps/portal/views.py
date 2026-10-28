from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import APIException
from apps.transfers.services import execute_transfer
from .forms import TransferForm
import uuid
import secrets
from django.views.decorators.http import require_POST
from apps.accounts.models import Account, Beneficiary
from apps.transfers.models import Transfer
from apps.loans.models import Loan
from apps.cards.models import Card
from apps.billing.models import BillPayment
from apps.investments.models import Holding

def signin(request):
    if request.user.is_authenticated:
        return redirect('portal-dashboard')
    form=AuthenticationForm(request, data=request.POST or None)
    if request.method=='POST' and form.is_valid():
        login(request,form.get_user())
        return redirect('portal-dashboard')
    return render(request,'portal/auth.html',{'form':form,'heading':'Sign in','submit':'Sign in'})

def signup(request):
    from apps.identity.models import User
    from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
    class RegistrationForm(BaseUserCreationForm):
        class Meta(BaseUserCreationForm.Meta):
            model=User
            fields=('username',)
    form=RegistrationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        login(request,user)
        return redirect('portal-dashboard')
    return render(request,'portal/auth.html',{'form':form,'heading':'Create account','submit':'Register'})

@require_POST
def signout(request):
    logout(request)
    return redirect('portal-login')

@login_required
def dashboard(request):
    accounts=Account.objects.filter(owner=request.user)
    transfers=Transfer.objects.filter(initiated_by=request.user).select_related('source','destination').order_by('-created_at')[:8]
    return render(request,'portal/dashboard.html',{'accounts':accounts,'transfers':transfers,'beneficiaries':Beneficiary.objects.filter(owner=request.user),'loans':Loan.objects.filter(owner=request.user),'cards':Card.objects.filter(account__owner=request.user),'bills':BillPayment.objects.filter(account__owner=request.user),'holdings':Holding.objects.filter(owner=request.user)})


@login_required
@require_POST
def open_account(request):
    Account.objects.create(owner=request.user,number='NS'+secrets.token_hex(10).upper(),currency='INR',balance=0,status='ACTIVE')
    messages.success(request,'Simulation account created. Initial balance is zero.')
    return redirect('portal-dashboard')

@login_required
def transfer_page(request):
    form=TransferForm(request.POST or None,user=request.user)
    if request.method=='POST' and form.is_valid():
        try:
            transfer,created=execute_transfer(user=request.user,source_id=form.cleaned_data['source'].pk,destination_id=form.cleaned_data['destination'].pk,amount=form.cleaned_data['amount'],key=str(uuid.uuid4()))
            if transfer.status=='COMPLETED':
                messages.success(request,'Transfer completed: '+str(transfer.pk))
            else:
                messages.error(request,'Transfer rejected: '+transfer.failure_reason)
            return redirect('portal-dashboard')
        except (APIException,ValueError,DjangoValidationError) as exc:
            form.add_error(None,str(exc))
    return render(request,'portal/transfer.html',{'form':form})

@login_required
def statement_page(request,account_id):
    from django.shortcuts import get_object_or_404
    from apps.ledger.models import LedgerEntry
    account=get_object_or_404(Account,pk=account_id,owner=request.user)
    entries=LedgerEntry.objects.filter(account=account).select_related('journal').order_by('-created_at')[:200]
    return render(request,'portal/statement.html',{'account':account,'entries':entries})

@login_required
def operations_page(request):
    from django.http import HttpResponseForbidden
    from apps.audit.models import AuditEvent
    from apps.risk.models import RiskAlert
    if request.user.role not in ('OPERATOR','APPROVER','ADMIN') and not request.user.is_superuser:
        return HttpResponseForbidden('Staff access required')
    return render(request,'portal/operations.html',{'alerts':RiskAlert.objects.order_by('-id')[:50],'events':AuditEvent.objects.order_by('-id')[:50]})


@login_required
def products_page(request):
    from django.http import HttpResponseForbidden
    from rest_framework.test import APIRequestFactory,force_authenticate
    from apps.loans.views import LoanViewSet
    from apps.cards.views import CardViewSet
    from apps.billing.views import BillViewSet
    from apps.investments.views import InvestmentViewSet
    from apps.operations.views import OperationsViewSet
    from apps.accounts.views import BeneficiaryViewSet
    from django.urls import reverse
    operations={
      'loan-apply':(LoanViewSet,'apply',False,['principal','annual_rate','term_months']),
      'loan-approve':(LoanViewSet,'approve',True,['id']),
      'loan-disburse':(LoanViewSet,'disburse',True,['id','account']),
      'loan-repay':(LoanViewSet,'repay',True,['id','account','amount','reference']),
      'card-issue':(CardViewSet,'issue',False,['account','daily_limit']),
      'card-freeze':(CardViewSet,'freeze',True,['id']),
      'card-activate':(CardViewSet,'activate',True,['id']),
      'card-block':(CardViewSet,'block',True,['id']),
      'bill-pay':(BillViewSet,'pay',False,['account','biller','reference','amount']),
      'investment-buy':(InvestmentViewSet,'buy',False,['account','symbol','quantity','simulated_unit_price']),
      'investment-sell':(InvestmentViewSet,'sell',False,['account','symbol','quantity','simulated_unit_price']),
      'deposit':(OperationsViewSet,'deposits',False,['account','amount','reference']),
      'verify-beneficiary':(OperationsViewSet,'verify_beneficiary',False,['beneficiary_id']),
      'beneficiary-add':(BeneficiaryViewSet,'create',False,['account','nickname']),
    }
    is_staff_operator=request.user.is_superuser or request.user.role in ('OPERATOR','APPROVER','ADMIN')
    if not is_staff_operator:
        operations={k:v for k,v in operations.items() if k not in ('deposit','verify-beneficiary','loan-approve','loan-disburse')}
    key=request.GET.get('action','loan-apply')
    if key not in operations:key='loan-apply'
    view,method,detail,fields=operations[key]
    staff=key in ('deposit','verify-beneficiary','loan-approve','loan-disburse')
    if staff and request.user.role not in ('OPERATOR','APPROVER','ADMIN') and not request.user.is_superuser:
        return HttpResponseForbidden('Staff access required')
    result=None;code=None
    if request.method=='POST':
        payload={field:request.POST.get(field,'') for field in fields if field!='id' and request.POST.get(field,'')!=''}
        factory=APIRequestFactory();internal=factory.post('/api/v1/',payload,format='json')
        force_authenticate(internal,user=request.user)
        kwargs={'pk':request.POST.get('id')} if detail else {}
        handler=view.as_view({'post':method})
        response=handler(internal,**kwargs)
        code=response.status_code;result=response.data
    return render(request,'portal/products.html',{'operations':operations,'selected':key,'fields':fields,'result':result,'code':code,'accounts':Account.objects.filter(owner=request.user),'loans':Loan.objects.filter(owner=request.user),'cards':Card.objects.filter(account__owner=request.user),'bills':BillPayment.objects.filter(account__owner=request.user),'holdings':Holding.objects.filter(owner=request.user),'beneficiaries':Beneficiary.objects.filter(owner=request.user)})
