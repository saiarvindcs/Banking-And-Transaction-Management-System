from rest_framework import generics, serializers
from apps.audit.models import AuditEvent
from apps.risk.models import RiskAlert
from apps.operations.views import StaffOnly

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model=AuditEvent
        fields='__all__'
class AuditList(generics.ListAPIView):
    permission_classes=[StaffOnly]
    serializer_class=AuditSerializer
    queryset=AuditEvent.objects.all().order_by('-id')

class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model=RiskAlert
        fields='__all__'
class RiskList(generics.ListAPIView):
    permission_classes=[StaffOnly]
    serializer_class=RiskSerializer
    queryset=RiskAlert.objects.all().order_by('-id')
