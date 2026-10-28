from rest_framework import serializers, permissions, generics
from django.db.models import Q
from apps.ledger.models import LedgerEntry
from apps.accounts.models import Account

class LedgerEntrySerializer(serializers.ModelSerializer):
    reference = serializers.CharField(source='journal.reference', read_only=True)
    class Meta:
        model = LedgerEntry
        fields = ['id','reference','side','amount','created_at','account']

class StatementView(generics.ListAPIView):
    serializer_class = LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return LedgerEntry.objects.filter(account_id=self.kwargs['id'], account__owner=self.request.user).select_related('journal').order_by('-created_at')
