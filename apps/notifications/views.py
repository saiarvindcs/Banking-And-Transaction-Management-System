from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from .models import OutboxEvent

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = ('id', 'topic', 'payload', 'created_at', 'delivered_at')
        read_only_fields = fields

class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return OutboxEvent.objects.filter(
            topic='IN_APP_NOTIFICATION', payload__user_id=self.request.user.pk
        ).order_by('-created_at', '-pk')
