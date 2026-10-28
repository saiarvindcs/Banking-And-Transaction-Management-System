
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.accounts.models import Account, Beneficiary
from apps.accounts.clearing import clearing_account
from apps.audit.models import AuditEvent
from apps.identity.models import User
from apps.ledger.models import Journal, LedgerEntry
from apps.risk.models import RiskAlert


class StaffOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.role in ("OPERATOR", "APPROVER", "ADMIN")
                or request.user.is_superuser
            )
        )


class DepositInput(serializers.Serializer):
    account = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=19,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    reference = serializers.RegexField(
        regex=r"^[A-Za-z0-9_-]{8,80}$",
        max_length=80,
    )


class WithdrawalInput(DepositInput):
    pass


class VerifyInput(serializers.Serializer):
    beneficiary_id = serializers.IntegerField(min_value=1)


class OperationsViewSet(viewsets.ViewSet):
    permission_classes = [StaffOnly]

    # BUG-001: Customers may access withdrawals.
    # All other operations remain staff-only.
    def get_permissions(self):
        if self.action == "withdrawals":
            return [permissions.IsAuthenticated()]

        return [StaffOnly()]

    def list(self, request):
        return Response({
            "risk_alerts_open": RiskAlert.objects.filter(
                resolved=False
            ).count(),
            "audit_events": AuditEvent.objects.count(),
            "journals": Journal.objects.count(),
        })

    @action(detail=False, methods=["get"])
    def reconciliation(self, request):
        bad = []

        for journal in (
            Journal.objects
            .prefetch_related("entries")
            .iterator(chunk_size=1000)
        ):
            debits = sum(
                (
                    entry.amount
                    for entry in journal.entries.all()
                    if entry.side == "DEBIT"
                ),
                Decimal("0.00"),
            )

            credits = sum(
                (
                    entry.amount
                    for entry in journal.entries.all()
                    if entry.side == "CREDIT"
                ),
                Decimal("0.00"),
            )

            if debits != credits:
                bad.append(str(journal.pk))

        return Response({
            "unbalanced_journals": bad,
            "count": len(bad),
        })

    @action(detail=False, methods=["get"])
    def risk(self, request):
        alerts = RiskAlert.objects.filter(
            resolved=False
        ).values("id", "resolved")

        return Response(list(alerts))

    @action(detail=False, methods=["get"])
    def audit(self, request):
        events = AuditEvent.objects.order_by("-id").values(
            "id",
            "action",
            "object_ref",
        )[:100]

        return Response(list(events))

    # ---------------------------
    # DEPOSITS - STAFF ONLY
    # ---------------------------

    @extend_schema(
        request=DepositInput,
        responses={201: dict, 200: dict},
    )
    @action(detail=False, methods=["post"], url_path="deposits")
    def deposits(self, request):
        data = DepositInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data

        with transaction.atomic():
            User.objects.select_for_update().get(
                pk=request.user.pk
            )

            reference = "DEPOSIT:" + values["reference"]

            previous = Journal.objects.filter(
                reference=reference
            ).first()

            if previous:
                entries = list(previous.entries.all())

                if len(entries) != 2 or not any(
                    entry.account_id == values["account"]
                    and entry.amount == values["amount"]
                    and entry.side == "CREDIT"
                    for entry in entries
                ):
                    raise ValidationError(
                        "Reference already used for another deposit"
                    )

                return Response({
                    "reference": reference,
                    "status": "ALREADY_POSTED",
                }, status=200)

            try:
                account = Account.objects.select_for_update().get(
                    pk=values["account"],
                    status="ACTIVE",
                )
            except Account.DoesNotExist:
                raise ValidationError({
                    "account": "Active account not found"
                })

            clearing = clearing_account()

            if account.pk == clearing.pk:
                raise ValidationError(
                    "Cannot fund clearing account"
                )

            journal = Journal.objects.create(
                reference=reference
            )

            LedgerEntry.objects.bulk_create([
                LedgerEntry(
                    journal=journal,
                    account=clearing,
                    side="DEBIT",
                    amount=values["amount"],
                ),
                LedgerEntry(
                    journal=journal,
                    account=account,
                    side="CREDIT",
                    amount=values["amount"],
                ),
            ])

            Account.objects.filter(pk=account.pk).update(
                balance=F("balance") + values["amount"]
            )

            AuditEvent.objects.create(
                actor=request.user,
                action="SIMULATED_DEPOSIT",
                object_ref=str(account.pk),
                details={
                    "amount": str(values["amount"]),
                    "reference": reference,
                },
            )

        return Response({
            "reference": reference,
            "account": str(account.pk),
            "amount": str(values["amount"]),
            "status": "POSTED",
        }, status=201)

    # ---------------------------
    # BENEFICIARY VERIFICATION
    # ---------------------------

    @extend_schema(
        request=VerifyInput,
        responses={200: dict},
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="verify-beneficiary",
    )
    def verify_beneficiary(self, request):
        data = VerifyInput(data=request.data)
        data.is_valid(raise_exception=True)

        try:
            beneficiary = (
                Beneficiary.objects
                .select_related("account")
                .get(
                    pk=data.validated_data["beneficiary_id"]
                )
            )
        except Beneficiary.DoesNotExist:
            raise ValidationError(
                "Beneficiary not found"
            )

        if beneficiary.account.status != "ACTIVE":
            raise ValidationError(
                "Account inactive"
            )

        beneficiary.verified = True
        beneficiary.save(
            update_fields=["verified"]
        )

        AuditEvent.objects.create(
            actor=request.user,
            action="BENEFICIARY_VERIFIED",
            object_ref=str(beneficiary.pk),
            details={},
        )

        return Response({
            "id": beneficiary.pk,
            "verified": beneficiary.verified,
        })

    # BUG-002: Hide old misspelled endpoint
    # from Swagger, but keep its URL working.
    
    @action(
        detail=False,
        methods=["post"],
        url_path="verify-benficiry",
        schema=None
    )
    @extend_schema(exclude=True)
    def verify_benficiry_legacy(self, request):
        return self.verify_beneficiary(request)

    # ---------------------------
    # WITHDRAWALS
    # ---------------------------

    @extend_schema(
        request=WithdrawalInput,
        responses={201: dict, 200: dict},
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="withdrawals",
    )
    def withdrawals(self, request):
        data = WithdrawalInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data

        with transaction.atomic():
            User.objects.select_for_update().get(
                pk=request.user.pk
            )

            # Lock the requested account first.
            try:
                account = (
                    Account.objects
                    .select_for_update()
                    .get(
                        pk=values["account"],
                        status="ACTIVE",
                    )
                )
            except Account.DoesNotExist:
                raise ValidationError({
                    "account": "Active account not found"
                })

            # BUG-001: Enforce account ownership
            # before checking payment references.
            is_staff = StaffOnly().has_permission(
                request, self
            )

            if not is_staff:
                if account.owner_id != request.user.pk:
                    raise PermissionDenied(
                        "You can withdraw only from your own account"
                    )

            clearing = clearing_account()

            if account.pk == clearing.pk:
                raise ValidationError(
                    "Cannot withdraw from clearing account"
                )

            reference = (
                "WITHDRAWAL:" + values["reference"]
            )

            # Idempotency: Never deduct twice
            # for the same withdrawal reference.
            previous = Journal.objects.filter(
                reference=reference
            ).first()

            if previous:
                entries = list(previous.entries.all())

                if len(entries) != 2 or not any(
                    entry.account_id == account.pk
                    and entry.amount == values["amount"]
                    and entry.side == "DEBIT"
                    for entry in entries
                ):
                    raise ValidationError(
                        "Reference already used for another withdrawal"
                    )

                return Response({
                    "reference": reference,
                    "status": "ALREADY_POSTED",
                }, status=200)

            if account.balance < values["amount"]:
                raise ValidationError(
                    "Insufficient funds"
                )

            journal = Journal.objects.create(
                reference=reference
            )

            LedgerEntry.objects.bulk_create([
                LedgerEntry(
                    journal=journal,
                    account=account,
                    side="DEBIT",
                    amount=values["amount"],
                ),
                LedgerEntry(
                    journal=journal,
                    account=clearing,
                    side="CREDIT",
                    amount=values["amount"],
                ),
            ])

            updated = Account.objects.filter(
                pk=account.pk,
                balance__gte=values["amount"],
            ).update(
                balance=F("balance") - values["amount"]
            )

            if updated != 1:
                raise ValidationError(
                    "Insufficient funds"
                )

            AuditEvent.objects.create(
                actor=request.user,
                action="SIMULATED_WITHDRAWAL",
                object_ref=str(account.pk),
                details={
                    "amount": str(values["amount"]),
                    "reference": reference,
                },
            )

        return Response({
            "reference": reference,
            "account": str(account.pk),
            "amount": str(values["amount"]),
            "status": "POSTED",
        }, status=201)
