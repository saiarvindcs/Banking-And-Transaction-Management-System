
from apps.notifications.models import OutboxEvent


def banking_notifications(request):
    if not request.user.is_authenticated:
        return {
            "notifications": [],
            "notification_count": 0,
        }

    events = (
        OutboxEvent.objects
        .filter(
            topic="IN_APP_NOTIFICATION",
            payload__user_id=request.user.pk,
        )
        .order_by("-created_at")[:10]
    )

    notifications = []

    for event in events:
        payload = event.payload or {}
        action = payload.get("action", "")
        details = payload.get("details", {})
        amount = details.get("amount")

        if action == "SIMULATED_WITHDRAWAL":
            title = "Withdrawal successful"
            message = f"₹{amount} withdrawn from your account."

        elif action == "TRANSFER_REVERSED":
            title = "Transfer reversed"
            message = f"Your ₹{amount} transfer was reversed."

        elif action == "SIMULATED_DEPOSIT":
            title = "Deposit successful"
            message = f"₹{amount} deposited into your account."

        else:
            title = action.replace("_", " ").title()
            message = "Your banking activity has been updated."

        notifications.append({
            "id": event.pk,
            "title": title,
            "message": message,
            "created_at": event.created_at,
        })

    return {
        "notifications": notifications,
        "notification_count": len(notifications),
    }
