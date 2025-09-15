import abc
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction as db_transaction

from .models import Wallet, Transaction


class InsufficientBalanceError(Exception):
    def __init__(self, message="Insufficient balance", available_balance=None):
        self.message = message
        self.available_balance = available_balance
        super().__init__(self.message)


from authentication.models import Organization


class WalletService(abc.ABC):
    @abc.abstractmethod
    def create_wallet(self, organization: Organization):
        pass

    @abc.abstractmethod
    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        pass

    @abc.abstractmethod
    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        pass

    @abc.abstractmethod
    def refund_wallet(self, original_transaction: Transaction):
        pass


class ProductionWalletService(WalletService):
    def create_wallet(self, organization: Organization):
        url = f"{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.create_wallet"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {settings.METER_SERVICES_TOKEN}",
        }
        data = {
            "party_name": organization.name,
            "reference": str(organization.uuid),
            "currency": str(organization.currency),
            "wallet_type": "Meter Wallet",
            "is_live": settings.IS_LIVE,
        }

        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "success":
            wallet_data = response_data["data"]
            wallet, _ = Wallet.objects.get_or_create(
                wallet_id=wallet_data["wallet_id"],
                defaults={
                    "created_by": wallet_data["owner"],
                    "reference": organization,
                    "currency": wallet_data["currency"],
                    "available_balance": wallet_data["available_balance"],
                }
            )
            return wallet

        if response.status_code == 400:
            error_message = str(response_data)
            if "Duplicate entry" in error_message or "IntegrityError" in error_message:
                # Wallet exists on the service but not locally, let's fetch it
                # This part needs a get_wallet implementation, for now let's raise
                raise Exception("Wallet already exists on the service.")

        raise Exception("Failed to create wallet: " + str(response_data))

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status='successful').exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='purchase',
            status='pending',
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}"
        )

        try:
            organization_id = wallet.reference.uuid
            url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.charge_wallet'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
            }
            data = {
                "debit_party": str(wallet.wallet_id),
                "credit_party": str(settings.CREDIT_WALLET_ID),
                "amount": float(amount),
                "debit_party_reference": str(organization_id),
                "is_live": settings.IS_LIVE
            }

            response = requests.post(url, json=data, headers=headers)
            response_data = response.json()

            if response.status_code != 200 or response_data.get('status') != 'success':
                err_type = response_data.get('data', {}).get('err_type')
                if err_type == "insufficient-balance":
                    raise InsufficientBalanceError(message=response_data.get("message"))
                else:
                    raise ValueError(f"Failed to charge wallet: {response_data.get('message')}")

            wallet.available_balance -= amount
            wallet.save()

            transaction.status = 'successful'
            transaction.save()

            return transaction

        except requests.exceptions.RequestException as e:
            transaction.status = 'failed'
            transaction.save()
            raise ValueError(f"Network error while charging wallet: {e}")
        except Exception as e:
            transaction.status = 'failed'
            transaction.save()
            raise e

    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        url = f'{settings.METER_SERVICES_URL}/api/method/meter_services.v1.wallet.initiate_payment'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'token {settings.METER_SERVICES_TOKEN}'
        }
        data = {
            'wallet_id': wallet.wallet_id,
            'amount': float(amount),
            'redirect_url': settings.FRONTEND_URL,
            'is_live': settings.IS_LIVE
        }

        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('status') == 'success':
            return response_data['data']['payment_options']

        raise Exception('Failed to initiate payment: ' + str(response_data))

    def refund_wallet(self, original_transaction: Transaction):
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(uuid=original_transaction.wallet.uuid)

            if Transaction.objects.filter(reference=original_transaction.transaction_id,
                                          transaction_type='refund').exists():
                return

            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                amount=original_transaction.amount,
                transaction_type='refund',
                status='successful',
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}"
            )

            wallet.available_balance += original_transaction.amount
            wallet.save()

            original_transaction.status = 'refunded'
            original_transaction.save()

            return refund_transaction


class SandboxWalletService(WalletService):
    def create_wallet(self, organization: Organization):
        wallet, created = Wallet.objects.get_or_create(
            reference=organization,
            defaults={
                "wallet_id": f"sandbox_{uuid.uuid4().hex}",
                "created_by": "sandbox@system.com",
                "currency": organization.currency or "NGN",
                "available_balance": Decimal("100000.00"),
                "ledger_balance": Decimal("100000.00"),
            }
        )
        if not created and wallet.available_balance == 0:
            wallet.available_balance = Decimal("100000.00")
            wallet.ledger_balance = Decimal("100000.00")
            wallet.save()

        return wallet

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status='successful').exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='purchase',
            status='pending',
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}"
        )

        if wallet.available_balance < amount:
            transaction.status = 'failed'
            transaction.save()
            raise InsufficientBalanceError("Insufficient balance in sandbox wallet")

        wallet.available_balance -= amount
        wallet.save()

        transaction.status = 'successful'
        transaction.save()

        return transaction

    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        with db_transaction.atomic():
            wallet.available_balance += amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='funding',
                status='successful',
                reference=f"SANDBOX-FUND-{uuid.uuid4().hex}",
                transaction_id=f"TXN-FUND-{uuid.uuid4().hex}"
            )

        return {"status": "success", "message": "Sandbox wallet topped up successfully."}

    def refund_wallet(self, original_transaction: Transaction):
        # Same as production for now
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(uuid=original_transaction.wallet.uuid)

            if Transaction.objects.filter(reference=original_transaction.transaction_id,
                                          transaction_type='refund').exists():
                return

            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                amount=original_transaction.amount,
                transaction_type='refund',
                status='successful',
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}"
            )

            wallet.available_balance += original_transaction.amount
            wallet.save()

            original_transaction.status = 'refunded'
            original_transaction.save()

            return refund_transaction


def get_wallet_service(organization):
    if organization.is_sandbox:
        return SandboxWalletService()
    return ProductionWalletService()
