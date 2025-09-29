from django.db import models

from authentication.models import User, Organization
from utils.models import TrackObjectStateMixin


class Meter(TrackObjectStateMixin):
    METER_TYPES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('gas', 'Gas'),
    ]
    customer_name = models.CharField(max_length=255)
    meter_number = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_code = models.CharField(
        max_length=10, blank=True, null=True, default=None
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    sgc = models.CharField(max_length=50, blank=True, null=True)
    tariff_index = models.CharField(max_length=10, blank=True, null=True)
    key_revision_number = models.CharField(max_length=10, blank=True, null=True)
    meter_type = models.CharField(choices=METER_TYPES, max_length=20)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='meters')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='meters')
    is_sandbox = models.BooleanField(default=True)

    def __str__(self):
        return f"Meter - {self.meter_number} - {self.organization.name}"


class UtilityCost(TrackObjectStateMixin):
    name = models.CharField(max_length=20, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.cost}"


class UtilityVend(TrackObjectStateMixin):
    TOKEN_TYPES = (
        ("credit", "Credit"),
        ("mse", "MSE"),
        ("mgtk", "MGTK"),
    )

    METER_TYPES = (
        ("electricity", "Electricity"),
        ("gas", "Gas"),
        ("water", "Water"),
    )
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name='vends')
    transaction = models.ForeignKey('wallet.Transaction', on_delete=models.SET_NULL, null=True, related_name='utility_vends')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    units = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    utility_cost = models.ForeignKey(UtilityCost, on_delete=models.SET_NULL, null=True, related_name='vends')
    vend_reference = models.CharField(max_length=100, unique=True)
    token = models.JSONField(default=list, blank=True)
    token_details = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')  # e.g., pending, successful, failed
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_vends')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='organization_vends')
    is_sandbox = models.BooleanField(default=True)
    token_type = models.CharField(choices=TOKEN_TYPES, max_length=20, null=True, blank=True)
    token_class = models.CharField(max_length=100, null=True, blank=True)
    token_sub_class = models.CharField(max_length=100, null=True, blank=True)
    meter_type = models.CharField(choices=METER_TYPES, max_length=20, null=True, blank=True)
    meter_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Vend - {self.vend_reference} - {self.meter.meter_number} - {self.amount}"