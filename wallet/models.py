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
    available_balance = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"Wallet - {self.wallet_id} - {self.reference.name}"



