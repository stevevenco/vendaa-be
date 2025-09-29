import requests
from django.conf import settings


class MeterServicesClient:
    def __init__(self):
        self.base_url = settings.METER_SERVICES_URL
        self.token = settings.METER_SERVICES_TOKEN
        self.is_live = settings.IS_LIVE
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {self.token}",
        }

    def create_wallet(self, party_name, reference, currency, wallet_type="Meter Wallet"):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.create_wallet"
        data = {
            "party_name": party_name,
            "reference": str(reference),
            "currency": str(currency),
            "wallet_type": wallet_type,
            "is_live": self.is_live,
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.status_code, response.json()

    def get_wallets(self, reference, currency, wallet_type="Meter Wallet"):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.get_wallets"
        params = {
            "wallet_type": wallet_type,
            "currency": str(currency),
            "reference": str(reference),
            "is_live": self.is_live,
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.status_code, response.json()

    def get_balance(self, wallet_id):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.get_balance"
        params = {"wallet_id": wallet_id, "is_live": self.is_live}
        response = requests.get(url, headers=self.headers, params=params)
        return response.status_code, response.json()

    def initiate_payment(self, wallet_id, amount, redirect_url):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.initiate_payment"
        data = {
            "wallet_id": wallet_id,
            "amount": float(amount),
            "redirect_url": redirect_url,
            "is_live": self.is_live,
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.status_code, response.json()

    def get_transactions(self, wallet_id, currency):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.get_transactions"
        params = {
            "party": wallet_id,
            "party_type": "wallet",
            "currency": str(currency),
            "is_live": self.is_live,
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.status_code, response.json()

    def get_single_transaction(self, transaction_id):
        # https://meterservices.01101960.xyz/api/method/meter_services.v1.wallet.fetch_transaction?transaction_id=12345678&is_live=0
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.fetch_transaction"
        params = {
            "transaction_id": str(transaction_id),
            "is_live": self.is_live,
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.status_code, response.json()

    def charge_wallet(self, debit_party, credit_party, amount, debit_party_reference):
        url = f"{self.base_url}/api/method/meter_services.v1.wallet.charge_wallet"
        data = {
            "debit_party": str(debit_party),
            "credit_party": str(credit_party),
            "amount": float(amount),
            "debit_party_reference": str(debit_party_reference),
            "is_live": self.is_live,
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.status_code, response.json()
