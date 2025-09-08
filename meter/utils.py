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
        print(f"Request failed: {e}")
        print(f"Response content: {response.json()}")
        response_body = response.json()
        # if response_body['response']['code'] == 500 and response_body.get("_server_messages"):
        #     raise serializers.ValidationError({"detail": "Invalid Meter Number"})
        # elif response_body['response']['code'] == 500 and response_body.get("message"):
        #     raise serializers.ValidationError({"detail": "Invalid Meter Number"})
        raise serializers.ValidationError({"detail": f"Failed to connect to meter service: {e}"})


def generate_meter_token(token_type, token_data):
    """
    Calls the external meter service to generate a token.
    """
    url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.generate_token"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }

    if token_type == "credit":
        token_data["subclass"] = 2
        token_data["ea"] = 7
        token_data["tct"] = 2
        token_data["sgc"] = 600675
        token_data["krn"] = 2
        token_data["ti"] = 10
        token_data["allow_krn_update"] = False
        token_data["key_expiry_number"] = 255
        token_data["use3kct"] = False
        token_data["allow_ken_update"] = False
    elif token_type == "kct":
        token_data["subclass"] = 2
        token_data["ea"] = 7
        token_data["tct"] = 2
        token_data["sgc"] = 600675
        token_data["krn"] = 2
        token_data["ti"] = 10
        token_data["allow_krn_update"] = False
        token_data["key_expiry_number"] = 255
        token_data["allow_ken_update"] = False
        token_data["to_sgc"] = 600675
        token_data["to_krn"] = 2
        token_data["to_ti"] = 12
    elif token_type == "clear_credit":
        token_data["token_type"] = "mse"
        token_data["subclass"] = 1
        token_data["ea"] = 7
        token_data["tct"] = 2
        token_data["sgc"] = 600675
        token_data["krn"] = 2
        token_data["ti"] = 10
        token_data["allow_krn_update"] = False
        token_data["key_expiry_number"] = 255
        token_data["use3kct"] = False
        token_data["allow_ken_update"] = False
    elif token_type == "clear_tamper":
        token_data["token_type"] = "mse"
        token_data["subclass"] = 5
        token_data["ea"] = 7
        token_data["tct"] = 2
        token_data["sgc"] = 600675
        token_data["krn"] = 2
        token_data["ti"] = 10
        token_data["allow_krn_update"] = False
        token_data["key_expiry_number"] = 255
        token_data["use3kct"] = False
        token_data["allow_ken_update"] = False

    try:
        response = requests.post(url, json=token_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise serializers.ValidationError({"detail": f"Failed to connect to meter service: {e}"})
