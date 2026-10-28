from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Loan, LoanPayment
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from apps.audit.models import AuditEvent
from .amortization import repayment_schedule

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['id','principal','annual_rate','term_months','status','created_at']
        read_only_fields = fields

class LoanApplicationSerializer(serializers.Serializer):
 principal=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('1000'))
 annual_rate=serializers.DecimalField(max_digits=6,decimal_places=3,min_value=Decimal('0'),max_value=Decimal('50'))
 term_months=serializers.IntegerField(min_value=1,max_value=360)

class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoanSerializer
    def get_queryset(self):
        return Loan.objects.filter(owner=self.request.user)
    @action(detail=True, methods=['get'], url_path='schedule')
    def schedule(self, request, pk=None):
        loan = self.get_object()
        return Response({'loan_id':loan.pk,'schedule':repayment_schedule(loan.principal,loan.annual_rate,loan.term_months)})

    @extend_schema(request=LoanApplicationSerializer,responses={201:LoanSerializer})
    @action(detail=False,methods=['post'],url_path='apply')
    def apply(self,request):
        data=LoanApplicationSerializer(data=request.data);data.is_valid(raise_exception=True)
        loan=Loan.objects.create(owner=request.user,**data.validated_data,status='APPLICATION')
        AuditEvent.objects.create(actor=request.user,action='LOAN_APPLIED',object_ref=str(loan.pk),details={})
        return Response(LoanSerializer(loan).data,status=201)
    @extend_schema(request=None,responses={200:LoanSerializer})
    @action(detail=True,methods=['post'],url_path='approve')
    def approve(self,request,pk=None):
        if request.user.role not in ('APPROVER','ADMIN') and not request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Approver role required')
        try: loan=Loan.objects.get(pk=pk)
        except Loan.DoesNotExist: from rest_framework.exceptions import NotFound; raise NotFound()
        if loan.status!='APPLICATION': raise ValidationError('Loan is not awaiting approval')
        loan.status='APPROVED';loan.save(update_fields=['status'])
        AuditEvent.objects.create(actor=request.user,action='LOAN_APPROVED',object_ref=str(loan.pk),details={})
        return Response(LoanSerializer(loan).data)


class LoanDisburseInput(serializers.Serializer):
    account=serializers.UUIDField()

class LoanRepayInput(serializers.Serializer):
    account=serializers.UUIDField()
    amount=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'))
    reference=serializers.RegexField(regex=r'^[A-Za-z0-9_-]{8,80}$',max_length=80)

@extend_schema(request=LoanDisburseInput,responses={200:LoanSerializer})
@action(detail=True,methods=['post'],url_path='disburse')
def disburse(self,request,pk=None):
    from django.db import transaction
    from django.db.models import F
    from apps.accounts.models import Account
    from apps.accounts.clearing import clearing_account
    from apps.ledger.models import Journal,LedgerEntry
    from rest_framework.exceptions import PermissionDenied
    if request.user.role not in ('APPROVER','ADMIN') and not request.user.is_superuser:
        raise PermissionDenied('Approver role required')
    data=LoanDisburseInput(data=request.data);data.is_valid(raise_exception=True)
    with transaction.atomic():
        try: loan=Loan.objects.select_for_update().get(pk=pk)
        except Loan.DoesNotExist: raise ValidationError('Loan not found')
        if loan.status!='APPROVED':raise ValidationError('Loan must be approved before disbursement')
        try: account=Account.objects.select_for_update().get(pk=data.validated_data['account'],owner=loan.owner,status='ACTIVE')
        except Account.DoesNotExist:raise ValidationError({'account':'Active borrower account required'})
        clearing=clearing_account()
        journal=Journal.objects.create(reference='LOAN_DISBURSE:'+str(loan.pk))
        LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=clearing,side='DEBIT',amount=loan.principal),LedgerEntry(journal=journal,account=account,side='CREDIT',amount=loan.principal)])
        Account.objects.filter(pk=account.pk).update(balance=F('balance')+loan.principal)
        loan.status='DISBURSED';loan.save(update_fields=['status'])
        AuditEvent.objects.create(actor=request.user,action='LOAN_DISBURSED',object_ref=str(loan.pk),details={'account':str(account.pk)})
    return Response(LoanSerializer(loan).data)

@extend_schema(request=LoanRepayInput,responses={201:dict,200:dict})
@action(detail=True,methods=['post'],url_path='repay')
def repay(self,request,pk=None):
    from django.db import transaction
    from django.db.models import F,Sum
    from apps.accounts.models import Account
    from apps.accounts.clearing import clearing_account
    from apps.ledger.models import Journal,LedgerEntry
    data=LoanRepayInput(data=request.data);data.is_valid(raise_exception=True);v=data.validated_data
    with transaction.atomic():
        try: loan=Loan.objects.select_for_update().get(pk=pk,owner=request.user)
        except Loan.DoesNotExist: raise ValidationError('Loan not found')
        if loan.status!='DISBURSED':raise ValidationError('Loan is not open for repayment')
        previous=LoanPayment.objects.filter(reference=v['reference']).first()
        if previous:
            if previous.loan_id!=loan.pk or previous.account_id!=v['account'] or previous.amount!=v['amount']:raise ValidationError('Reference reused with different details')
            return Response({'id':previous.pk,'status':'ALREADY_POSTED'},status=200)
        total_due=sum(Decimal(row['payment']) for row in repayment_schedule(loan.principal,loan.annual_rate,loan.term_months))
        paid=loan.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        remaining=total_due-paid
        if v['amount']>remaining:raise ValidationError('Amount exceeds outstanding scheduled repayments')
        try:account=Account.objects.select_for_update().get(pk=v['account'],owner=request.user,status='ACTIVE')
        except Account.DoesNotExist:raise ValidationError('Active account not found')
        if account.balance<v['amount']:raise ValidationError('Insufficient funds')
        payment=LoanPayment.objects.create(loan=loan,account=account,amount=v['amount'],reference=v['reference'])
        clearing=clearing_account()
        journal=Journal.objects.create(reference='LOAN_REPAY:'+v['reference'])
        LedgerEntry.objects.bulk_create([LedgerEntry(journal=journal,account=account,side='DEBIT',amount=v['amount']),LedgerEntry(journal=journal,account=clearing,side='CREDIT',amount=v['amount'])])
        Account.objects.filter(pk=account.pk).update(balance=F('balance')-v['amount'])
        if remaining-v['amount']<=Decimal('0.00'):
            loan.status='REPAID';loan.save(update_fields=['status'])
        AuditEvent.objects.create(actor=request.user,action='LOAN_REPAYMENT',object_ref=str(loan.pk),details={'payment':str(payment.pk)})
    return Response({'id':payment.pk,'remaining_scheduled_due':str(remaining-v['amount']),'loan_status':loan.status},status=201)

LoanViewSet.disburse=disburse
LoanViewSet.repay=repay
