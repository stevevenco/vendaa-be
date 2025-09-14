from django.db import models

# Create your models here.
from django.db import models
from utils.models import TrackObjectStateMixin

class Country(TrackObjectStateMixin):
    name = models.CharField(max_length=255, unique=True)
    currency = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} ({self.currency})"
