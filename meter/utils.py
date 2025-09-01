import requests
from django.conf import settings

from meter.models import Meter

def add_meter_to_service(validated_data):
    """
    Calls the external meter service to add a new meter.
    """
    url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.add_meter"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    data = {
        "meter": validated_data.get('meter_number')
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        print(f"\n\nResponse data: {response_data}\n\n")

        if response.status_code == 200 and response_data["response"].get('status') == 'success':
            meter = Meter.objects.create(**validated_data)
            return meter
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, etc.
        raise Exception("Failed to add meter to service", str(e))
