# Hadnle business logic deaing with payments here

from decimal import Decimal

import requests
from django.conf import settings
from django.http import JsonResponse


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
BASE_URL = "https://api.paystack.co"


def update_wallet(user, amount, transaction_type):
    """
    Updates the user's wallet balance based on the transaction type.
    """
    wallet = user.wallet
    if transaction_type == "payment":
        wallet.balance += Decimal(amount)
    elif transaction_type in ["withdraw"]:
        wallet.balance -= Decimal(amount)
    wallet.save()
    return wallet


def create_transaction(user, amount, transaction_type, recipient_id):
    """
    Creates a transaction record based on the transaction type.
    """

    # register transaction in DB
    pass


def initiate_payment_gateway(user, transaction_id, amount):
    """
    Interacts with the Paystack API to initiate a deposit.
    """
    url = f"{BASE_URL}/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "amount": int(amount * 100),  # Paystack expects amount in kobo
        "email": user.email,
        "currency": "NGN",
        "metadata": {
            "transaction_id": str(transaction_id),
            # "user_id": str(self.context['request'].user.id),
            "transaction_type": "deposit",
        },
    }

    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    # Handle possible errors from Le'Paystack
    if response.status_code != 200 or not response_data["status"]:
        return JsonResponse(
            {"error": "Failed to initiate payment with Paystack."}, status=500
        )

    return response_data


def create_paystack_recipient(account_number, bank_code, name):
    url = f"{BASE_URL}/transferrecipient"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    data = {
        "type": "nuban",
        "name": name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN",
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def initiate_withdraw(amount, recipient_code, reference):
    url = f"{BASE_URL}/transfer"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    print(f"recipient_code: {recipient_code}")
    data = {
        "source": "balance",
        "amount": int(amount * 100),  # Convert to kobo
        "recipient": str(recipient_code),
        "reference": str(reference),
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
