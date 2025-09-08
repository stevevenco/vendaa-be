import requests
from django.conf import settings

from wallet.serializers import TransactionSerializer
from .models import Wallet

def create_wallet_for_organization(org):
    """
    Creates a wallet for an organization using the meter services API.
    If the wallet already exists on Meter Services but not in our DB,
    fetches it and saves it locally.

    Args:
        org: Organization instance

    Returns:
        Wallet instance if successful
    """
    url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.create_wallet"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {settings.METER_SERVICES_TOKEN}",
    }
    data = {
        "party_name": org.name,
        "reference": str(org.uuid),
        "currency": "NGN",
        "wallet_type": "Meter Wallet",
        "is_live": 0,
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    # ✅ Case 1: Success — create wallet in DB
    if response.status_code == 200 and response_data.get("status") == "success":
        wallet_data = response_data["data"]
        wallet = Wallet.objects.create(
            wallet_id=wallet_data["wallet_id"],
            created_by=wallet_data["owner"],
            reference=org,
            currency=wallet_data["currency"],
            available_balance=wallet_data["available_balance"],
        )
        return wallet

    # ✅ Case 2: Duplicate wallet error (wallet exists in meter services but not in DB)
    if response.status_code == 400:
        error_message = str(response_data)
        if "Duplicate entry" in error_message or "IntegrityError" in error_message:
            return get_wallet_for_organization(org)

    # ❌ Case 3: General failure
    raise Exception("Failed to create wallet: " + str(response_data))


def get_wallet_for_organization(org):
    """
    Retrieves an organization's wallet from Meter Services and stores it in our DB.
    
    Args:
        org: Organization instance
        
    Returns:
        Wallet instance if successful
    """
    url = (
        f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.get_wallets"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {settings.METER_SERVICES_TOKEN}",
    }
    params = {
        'wallet_type': "Meter Wallet",
        'currency': "NGN",
        'reference': org.uuid,
        'is_live': 0
    }

    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()

    if response.status_code == 200 and response_data.get("status") == "success":
        wallets = response_data.get("data", [])
        if not wallets:
            raise Exception(f"No wallet found for organization {org.uuid}")

        wallet_data = wallets[0]  # expect one wallet per org reference

        # Save in DB
        wallet = Wallet.objects.create(
            wallet_id=wallet_data["wallet_id"],
            created_by=wallet_data["owner"],
            reference=org,
            currency=wallet_data["currency"],
            available_balance=wallet_data["available_balance"],
        )
        return wallet

    raise Exception("Failed to retrieve wallet: " + str(response_data))


def get_wallet_balance(wallet_id):
    """
    Gets the wallet balance from meter services API
    
    Args:
        wallet_id: The wallet ID to check
        
    Returns:
        Decimal balance value
        
    Raises:
        Exception if balance check fails
    """
    url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.get_balance'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    params = {
        'wallet_id': wallet_id,
        'is_live': 0
    }

    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()
    print(f"\n\nresponse_data: {response_data}\n\n")

    if response.status_code == 200 and response_data.get('status') == 'success':
        balance_data = response_data['data']
        return balance_data['avail_balance_cur']
    
    raise Exception('Failed to get wallet balance: ' + str(response_data))

def initiate_wallet_payment(wallet_id, amount):
    """
    Initiates a payment for wallet funding
    
    Args:
        wallet_id: The wallet ID to fund
        amount: Amount to fund
        
    Returns:
        Dict with payment options
        
    Raises:
        Exception if payment initiation fails
    """
    url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.initiate_payment'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    data = {
        'wallet_id': wallet_id,
        'amount': amount,
        'redirect_url': settings.FRONTEND_URL,
        'is_live': 0
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response.status_code == 200 and response_data.get('status') == 'success':
        return response_data['data']['payment_options']
    
    raise Exception('Failed to initiate payment: ' + str(response_data))


def get_wallet_transaction_history(wallet_id):
    """
    Retrieves the transaction history for a wallet from Meter Services.
    
    Args:
        wallet_id: The wallet ID to fetch transactions for.
        
    Returns:
        List of transaction dicts.
        
    Raises:
        Exception if fetching transactions fails.
    """
    url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.get_transactions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    params = {
        'party': wallet_id,
        'party_type': 'wallet',
        'currency': 'NGN',
        'is_live': 0
    }

    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()

    if response.status_code == 200 and response_data.get('status') == 'success':
        res_data = response_data['data']
        # print(f"\n\nres_data: {res_data}\n\n")
        # return [TransactionSerializer(txn).data for txn in res_data]
        return res_data

    raise Exception('Failed to fetch transactions: ' + str(response_data))