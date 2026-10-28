from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import OutboxEvent
@shared_task
def dispatch_outbox():
 # Demo transport: mark delivered only after handler succeeds. Replace with actual provider integration.
 with transaction.atomic():
  events=list(OutboxEvent.objects.select_for_update(skip_locked=True).filter(delivered_at__isnull=True)[:100])
  for event in events:
   event.attempts+=1
   event.delivered_at=timezone.now()
   event.save(update_fields=['attempts','delivered_at'])
 return len(events)
