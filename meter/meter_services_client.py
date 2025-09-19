# meter/meter_services_client.py
import requests
from django.conf import settings
from rest_framework import serializers


class MeterServicesClient:
    """
    Thin HTTP client for the external Meter Services API.
    """

    def __init__(self):
        self.base_url = settings.METER_SERVICES_URL
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'token {settings.METER_SERVICES_TOKEN}',
        }

    def add_meter(self, meter_number: str):
        url = f"{self.base_url}/api/method/meter_services.v1.add_meter"
        data = {"meter": meter_number}
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(
                {"detail": f"Failed to connect to meter service: {e}"}
            )

    def generate_token(self, token_data: dict):
        url = f"{self.base_url}/api/method/meter_services.v1.generate_token"
        try:
            response = requests.post(url, json=token_data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(
                f"Failed to connect to meter service: {e}"
            )
