from rest_framework import serializers
import requests
from django.conf import settings

from authentication.models import Organization
from .models import Meter


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = '__all__'
        read_only_fields = ['uuid', 'added_by', 'created', 'last_updated']