from django.db import models

from authentication.models import User
from utils.models import TrackObjectStateMixin

'''
Customer Name
Enter customer name
Meter Number
Enter meter number
Email
customer@example.com
Phone
+234-xxx-xxx-xxxx
Address
Enter customer address
SGC
Enter SGC
Tariff Index
T1, T2, etc.
Key Revision Number
001, 002, etc.
Meter Type
'''

class Meter(TrackObjectStateMixin):
    meter_types = [
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
    meter_type = models.Choices(choices=meter_types, default='electricity', max_length=20)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='meters')

    def __str__(self):
        return f"Meter - {self.meter_number} - {self.customer_name}"
