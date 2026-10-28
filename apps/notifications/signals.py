"""Persist user-facing notifications when audited banking actions complete."""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from apps.audit.models import AuditEvent
from .models import OutboxEvent

logger = logging.getLogger(__name__)
NOTIFIABLE = {
    'TRANSFER_COMPLETED', 'TRANSFER_REJECTED', 'TRANSFER_REVERSED',
    'LOAN_APPLIED', 'LOAN_APPROVED', 'LOAN_DISBURSED', 'LOAN_REPAYMENT',
    'CARD_ISSUED', 'CARD_FROZEN', 'CARD_BLOCKED',
    'SIMULATED_BILL_PAYMENT', 'PAPER_TRADE_BUY', 'PAPER_TRADE_SELL',
    'SIMULATED_DEPOSIT', 'SIMULATED_WITHDRAWAL',
}

@receiver(post_save, sender=AuditEvent, dispatch_uid='banking_outbox_on_audit')
def create_notification(sender, instance, created, **kwargs):
    if not created or instance.action not in NOTIFIABLE:
        return
    # Staff-initiated actions can target a customer's account. Prefer the
    # account owner when the audited object_ref is an account UUID.
    recipient_id = instance.actor_id
    if instance.action in ('SIMULATED_DEPOSIT', 'SIMULATED_WITHDRAWAL'):
        from apps.accounts.models import Account
        recipient_id = (Account.objects.filter(pk=instance.object_ref)
                        .values_list('owner_id', flat=True).first() or recipient_id)
    elif instance.action == 'TRANSFER_REVERSED':
        from apps.transfers.models import Transfer
        recipient_id = (Transfer.objects.filter(pk=instance.object_ref)
                        .values_list('initiated_by_id', flat=True).first() or recipient_id)
    elif instance.action in ('LOAN_APPROVED', 'LOAN_DISBURSED'):
        from apps.loans.models import Loan
        recipient_id = (Loan.objects.filter(pk=instance.object_ref)
                        .values_list('owner_id', flat=True).first() or recipient_id)
    if not recipient_id:
        return
    OutboxEvent.objects.create(topic='IN_APP_NOTIFICATION', payload={
        'user_id': recipient_id,
        'action': instance.action,
        'object_ref': instance.object_ref,
        'details': instance.details,
        'audit_id': instance.pk,
    })
    def queue_delivery():
        try:
            from .tasks import dispatch_outbox
            dispatch_outbox.delay()
        except Exception:
            # A notification broker outage must not turn a committed bank
            # transaction into a client-visible 500 error.
            logger.exception('Notification dispatch scheduling failed')
    transaction.on_commit(queue_delivery)
