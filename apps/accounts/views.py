import secrets
from rest_framework import viewsets, serializers
from .models import Account, Beneficiary

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id','number','currency','balance','status','daily_limit','created_at']
        read_only_fields = fields

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    http_method_names = ['get','post','head','options']
    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,number='NS'+secrets.token_hex(10).upper(),balance=0,status='ACTIVE',currency='INR')

class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = ['id','account','nickname','verified','created_at']
        read_only_fields = ['verified','created_at']
    def validate_account(self, account):
        if account.owner_id == self.context['request'].user.pk:
            raise serializers.ValidationError('Cannot add your own account as a beneficiary')
        if account.status != 'ACTIVE':
            raise serializers.ValidationError('Beneficiary account is not active')
        return account

class BeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = BeneficiarySerializer
    def get_queryset(self):
        return Beneficiary.objects.filter(owner=self.request.user)
    def perform_create(self,serializer):
        serializer.save(owner=self.request.user)
