import uuid
from decimal import Decimal
from django.db import transaction as db_transaction
from requests.exceptions import RequestException
from wallet.models import Wallet, Transaction
from wallet.meter_services_client import charge_wallet

class InsufficientBalanceError(Exception):
    def __init__(self, message="Insufficient balance", available_balance=None):
        self.message = message
        self.available_balance = available_balance
        super().__init__(self.message)

class ChargeService:
    @staticmethod
    def debit_wallet(wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        """
        Debits a wallet for a given amount.
        This method should be called within a transaction.
        """
        # Idempotency Check
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status='successful').exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        # Create a transaction record
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
            # Debit the wallet using the external service
            charge_response = charge_wallet(wallet.wallet_id, float(amount), idempotency_key)
            print(f"Charge Response: {charge_response}")

            if charge_response.get("status") != "success":
                err_type = charge_response.get("err_type")
                print(f"Error Type: {err_type}")
                if err_type == "insufficient-balance":
                    # available_balance = charge_response.get("data", {}).get("available_balance")
                    raise InsufficientBalanceError(
                        message=charge_response.get("message"),
                        # available_balance=available_balance
                    )
                    # raise ValueError(charge_response.get("message"))
                else:
                    raise ValueError(f"Failed to charge wallet: {charge_response.get('message')}")

            # Update wallet balance and transaction status
            wallet.available_balance -= amount
            wallet.save()

            transaction.status = 'successful'
            transaction.save()

            return transaction

        except RequestException as e:
            transaction.status = 'failed'
            transaction.save()
            raise ValueError(f"Network error while charging wallet: {e}")
        except Exception as e:
            transaction.status = 'failed'
            transaction.save()
            raise e

    @staticmethod
    def refund_wallet(original_transaction: Transaction):
        """
        Refunds a transaction.

        Args:
            original_transaction: The transaction to refund.

        Returns:
            The created refund transaction.
        """
        with db_transaction.atomic():
            # 1. Lock the wallet row
            wallet = Wallet.objects.select_for_update().get(uuid=original_transaction.wallet.uuid)

            # 2. Check if the transaction has already been refunded
            if Transaction.objects.filter(reference=original_transaction.transaction_id, transaction_type='refund').exists():
                # Already refunded
                return

            # 3. Create a refund transaction
            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                amount=original_transaction.amount,
                transaction_type='refund',
                status='successful',
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}"
            )

            # 4. Credit the wallet
            wallet.available_balance += original_transaction.amount
            wallet.save()

            # 5. Update the original transaction's status
            original_transaction.status = 'refunded'
            original_transaction.save()

            return refund_transaction
