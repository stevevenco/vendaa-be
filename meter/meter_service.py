# meter/services.py
import abc
import random
import string
from rest_framework import serializers

from authentication.models import Organization
from meter.models import Meter
from meter.meter_services_client import MeterServicesClient


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
    def __init__(self):
        self.client = MeterServicesClient()

    def _prepare_token_data(self, token_type, token_data, meter):
        """
        Injects meter-specific fields depending on token type.
        """
        if token_type == "credit":
            token_data.update({
                "subclass": 2,
                "ea": 7,
                "tct": 2,
                "sgc": meter.sgc,
                "krn": meter.key_revision_number,
                "ti": meter.tariff_index,
                "allow_krn_update": False,
                "key_expiry_number": 255,
                "use3kct": False,
                "allow_ken_update": False,
            })
        elif token_type == "kct":
            token_data.update({
                "subclass": 2,
                "ea": 7,
                "tct": 2,
                "sgc": meter.sgc,
                "krn": meter.key_revision_number,
                "ti": meter.tariff_index,
                "allow_krn_update": False,
                "key_expiry_number": 255,
                "allow_ken_update": False,
                "to_sgc": meter.sgc,
                "to_krn": meter.key_revision_number,
                "to_ti": meter.tariff_index,
            })
        elif token_type == "clear_credit":
            token_data.update({
                "token_type": "mse",
                "subclass": 1,
                "ea": 7,
                "tct": 2,
                "sgc": meter.sgc,
                "krn": meter.key_revision_number,
                "ti": meter.tariff_index,
                "allow_krn_update": False,
                "key_expiry_number": 255,
                "use3kct": False,
                "allow_ken_update": False,
            })
        elif token_type == "clear_tamper":
            token_data.update({
                "token_type": "mse",
                "subclass": 5,
                "ea": 7,
                "tct": 2,
                "sgc": meter.sgc,
                "krn": meter.key_revision_number,
                "ti": meter.tariff_index,
                "allow_krn_update": False,
                "key_expiry_number": 255,
                "use3kct": False,
                "allow_ken_update": False,
            })
        elif token_type == "mgtk":
            token_data.update({
                "token_type": "mse",
                "subclass": 10,
                "ea": 7,
                "tct": 2,
                "sgc": meter.sgc,
                "krn": meter.key_revision_number,
                "ti": meter.tariff_index,
                "allow_krn_update": False,
                "key_expiry_number": 255,
                "use3kct": False,
                "allow_ken_update": False,
            })

        if "amount" in token_data:
            token_data["amount"] = float(token_data["amount"])

        return token_data

    def generate_token(self, token_type, token_data, meter):
        prepared_data = self._prepare_token_data(token_type, token_data, meter)
        return self.client.generate_token(prepared_data)

    def add_meter(self, meter_number):
        return self.client.add_meter(meter_number)

    def disconnect_meter(self, meter_number):
        raise NotImplementedError("Disconnect meter is not implemented for production service yet.")

    def reconnect_meter(self, meter_number):
        raise NotImplementedError("Reconnect meter is not implemented for production service yet.")


class SandboxMeterService(MeterService):
    def generate_token(self, token_type, token_data, meter):
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

    def create_demo_meters(self, organization: Organization):
        for i in range(5):
            meter_number = f'SANDBOX-{random.randint(1000000000, 9999999999)}'
            Meter.objects.get_or_create(
                meter_number=meter_number,
                organization=organization,
                defaults={
                    'customer_name': f'Sandbox Customer {i + 1}',
                    'address': f'123 Sandbox Street, Demo City',
                    'meter_type': 'electricity',
                    'sgc': '12345',
                    'tariff_index': '1',
                    'key_revision_number': '1',
                }
            )

    def add_meter(self, meter_number):
        return {"response": {"status": "success", "message": f"Sandbox meter {meter_number} added successfully."}}

    def disconnect_meter(self, meter_number):
        return {"status": "success", "message": f"Sandbox meter {meter_number} disconnected successfully."}

    def reconnect_meter(self, meter_number):
        return {"status": "success", "message": f"Sandbox meter {meter_number} reconnected successfully."}


def get_meter_service(organization):
    if organization.is_sandbox:
        return SandboxMeterService()
    return ProductionMeterService()
