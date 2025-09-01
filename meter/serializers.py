from rest_framework import serializers
import requests
from django.conf import settings

from authentication.models import Organization
from .models import Meter

from meter.utils import add_meter_to_service


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = '__all__'
        read_only_fields = ['uuid', 'added_by', 'created', 'last_updated']

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        try:
            return add_meter_to_service(validated_data)
        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})