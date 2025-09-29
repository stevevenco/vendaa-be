from django.db import models

# Create your models here.
from django.db import models
from utils.models import TrackObjectStateMixin

class Country(TrackObjectStateMixin):
    name = models.CharField(max_length=255, unique=True)
    currency = models.CharField(max_length=10)
    currency_symbol = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"
