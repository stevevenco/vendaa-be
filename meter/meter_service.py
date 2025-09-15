import abc
import random
import string
import requests
from django.conf import settings
from rest_framework import serializers

class MeterService(abc.ABC):
    @abc.abstractmethod
    def generate_token(self, token_type, token_data, meter):
        pass

    @abc.abstractmethod
    def add_meter(self, meter_number):
        pass

    @abc.abstractmethod
    def disconnect_meter(self, meter_number):
        pass

    @abc.abstractmethod
    def reconnect_meter(self, meter_number):
        pass


class ProductionMeterService(MeterService):
    def generate_token(self, token_type, token_data, meter):
        url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.generate_token"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
        }

        if token_type == "credit":
            token_data["subclass"] = 2
            token_data["ea"] = 7
            token_data["tct"] = 2
            token_data["sgc"] = meter.sgc
            token_data["krn"] = meter.key_revision_number
            token_data["ti"] = meter.tariff_index
            token_data["allow_krn_update"] = False
            token_data["key_expiry_number"] = 255
            token_data["use3kct"] = False
            token_data["allow_ken_update"] = False
        elif token_type == "kct":
            token_data["subclass"] = 2
            token_data["ea"] = 7
            token_data["tct"] = 2
            token_data["sgc"] = meter.sgc
            token_data["krn"] = meter.key_revision_number
            token_data["ti"] = meter.tariff_index
            token_data["allow_krn_update"] = False
            token_data["key_expiry_number"] = 255
            token_data["allow_ken_update"] = False
            token_data["to_sgc"] = meter.sgc
            token_data["to_krn"] = meter.key_revision_number
            token_data["to_ti"] = meter.tariff_index
        elif token_type == "clear_credit":
            token_data["token_type"] = "mse"
            token_data["subclass"] = 1
            token_data["ea"] = 7
            token_data["tct"] = 2
            token_data["sgc"] = meter.sgc
            token_data["krn"] = meter.key_revision_number
            token_data["ti"] = meter.tariff_index
            token_data["allow_krn_update"] = False
            token_data["key_expiry_number"] = 255
            token_data["use3kct"] = False
            token_data["allow_ken_update"] = False
        elif token_type == "clear_tamper":
            token_data["token_type"] = "mse"
            token_data["subclass"] = 5
            token_data["ea"] = 7
            token_data["tct"] = 2
            token_data["sgc"] = meter.sgc
            token_data["krn"] = meter.key_revision_number
            token_data["ti"] = meter.tariff_index
            token_data["allow_krn_update"] = False
            token_data["key_expiry_number"] = 255
            token_data["use3kct"] = False
            token_data["allow_ken_update"] = False

        if 'amount' in token_data:
            token_data['amount'] = float(token_data['amount'])

        try:
            response = requests.post(url, json=token_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(f"Failed to connect to meter service: {e}")

    def add_meter(self, meter_number):
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
            raise serializers.ValidationError({"detail": f"Failed to connect to meter service: {e}"})

    def disconnect_meter(self, meter_number):
        raise NotImplementedError("Disconnect meter is not implemented for production service yet.")

    def reconnect_meter(self, meter_number):
        raise NotImplementedError("Reconnect meter is not implemented for production service yet.")


class SandboxMeterService(MeterService):
    def generate_token(self, token_type, token_data, meter):
        # Generate a random 20-digit token
        token = ''.join(random.choices(string.digits, k=20))
        return {
            "data": {
                "data": [
                    {
                        "tokenDec": token,
                        "description": "Sandbox Token"
                    }
                ]
            }
        }

    def add_meter(self, meter_number):
        return {"status": "success", "message": f"Sandbox meter {meter_number} added successfully."}

    def disconnect_meter(self, meter_number):
        return {"status": "success", "message": f"Sandbox meter {meter_number} disconnected successfully."}

    def reconnect_meter(self, meter_number):
        return {"status": "success", "message": f"Sandbox meter {meter_number} reconnected successfully."}


def get_meter_service(organization):
    if organization.is_sandbox:
        return SandboxMeterService()
    return ProductionMeterService()
