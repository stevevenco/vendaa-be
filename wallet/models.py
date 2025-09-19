from django.db import models

from django.conf import settings

from authentication.models import Organization
from utils.models import TrackObjectStateMixin


class Wallet(TrackObjectStateMixin):
    wallet_id = models.CharField(max_length=100)
    created_by = models.EmailField()
    reference = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="wallets"
    )
    currency = models.CharField(max_length=3)
    available_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    ledger_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet - {self.wallet_id} - {self.reference.name}"


class Transaction(TrackObjectStateMixin):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
        ('funding', 'Funding'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    EVENT_TYPES = [
        ('fund', 'Fund'),
        ('charge', 'Charge'),
        ('unspecified', 'Unspecified'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, blank=True, null=True)
    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)
    event = models.CharField(max_length=100, null=True, blank=True, choices=TRANSACTION_TYPES, default='unspecified')
    title = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Transaction - {self.transaction_id} - {self.status}"

