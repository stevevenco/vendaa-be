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
    meter_number = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    sgc = models.CharField(max_length=50, blank=True, null=True)
    tariff_index = models.CharField(max_length=10, blank=True, null=True)
    key_revision_number = models.CharField(max_length=10, blank=True, null=True)
    meter_type = models.CharField(choices=METER_TYPES, max_length=20)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='meters')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='meters')

    def __str__(self):
        return f"Meter - {self.meter_number} - {self.customer_name}"
