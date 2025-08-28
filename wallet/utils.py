import requests
from django.conf import settings
from .models import Wallet

def create_wallet_for_organization(org):
    """
    Creates a wallet for an organization using the meter services API
    
    Args:
        org: Organization instance
        
    Returns:
        Wallet instance if successful
        
    Raises:
        Exception if wallet creation fails
    """
    url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.create_wallet'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
    }
    data = {
        'party_name': org.name,
        'reference': str(org.uuid),
        'currency': 'NGN',
        'wallet_type': 'Meter Wallet',
        'is_live': 0
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()

    if response.status_code == 200 and response_data.get('status') == 'success':
        wallet_data = response_data['data']
        wallet = Wallet.objects.create(
            wallet_id=wallet_data['wallet_id'],
            created_by=wallet_data['owner'],
            reference=org,
            currency=wallet_data['currency'],
            available_balance=wallet_data['available_balance']
        )
        return wallet

    raise Exception('Failed to create wallet: ' + str(response_data))

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