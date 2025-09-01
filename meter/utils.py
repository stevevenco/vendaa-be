import requests
from django.conf import settings
from rest_framework import serializers

def add_meter_to_service(meter_number):
    """
    Calls the external meter service to add a new meter.
    """
    url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.add_meter"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    data = {
        "meter": meter_number
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, etc.
        raise serializers.ValidationError({"detail": f"Failed to connect to meter service: {e}"})


def generate_meter_token(token_data):
    """
    Calls the external meter service to generate a token.
    """
    url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.generate_token"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    try:
        response = requests.post(url, json=token_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise serializers.ValidationError({"detail": f"Failed to connect to meter service: {e}"})
