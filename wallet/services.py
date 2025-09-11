import uuid
from decimal import Decimal
from django.db import transaction as db_transaction
from wallet.models import Wallet, Transaction
from wallet.utils import get_wallet_balance, charge_wallet
class ChargeService:
    @staticmethod
    def debit_wallet(wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        """
        Debits a wallet for a given amount in an atomic and idempotent way.
        """
        # 1. Idempotency Check
        if idempotency_key:
            if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
                raise ValueError("Duplicate request: Transaction with this idempotency key already exists.")
                # return Transaction.objects.get(idempotency_key=idempotency_key)

        # 2. Check for sufficient funds
        external_balance_str = get_wallet_balance(wallet.wallet_id)
        # Clean up the balance string to decimal for comparison
        cleaned_balance = external_balance_str.replace('₦', '').replace(',', '').strip()
        balance_decimal = Decimal(cleaned_balance)

        print(f"\n\nOutside Lock: External Balance: {balance_decimal}, Amount to Debit: {amount}")

        if balance_decimal < amount:
            # Create a failed transaction for auditing purposes
            # Transaction.objects.create(
            #     wallet=wallet,
            #     amount=amount,
            #     transaction_type='purchase',
            #     status='failed',
            #     reference=reference,
            #     idempotency_key=idempotency_key,
            #     transaction_id=f"TXN-{uuid.uuid4().hex}"
            # )
            print("\n\nInsufficient funds - Transaction Failed")
            raise ValueError("Insufficient funds")

        with db_transaction.atomic():
            # 3. Lock the wallet row for the duration of the transaction
            wallet_to_debit = Wallet.objects.select_for_update().get(uuid=wallet.uuid)

            # Re-check funds inside the transaction to be safe
            external_balance_str_re_check = get_wallet_balance(wallet_to_debit.wallet_id)
            cleaned_balance_re_check = external_balance_str_re_check.replace('₦', '').replace(',', '').strip()
            balance_decimal_re_check = Decimal(cleaned_balance_re_check)

            print(f"\n\nInside Lock: External Balance: {balance_decimal_re_check}, Amount to Debit: {amount}")

            if balance_decimal_re_check < amount:
                raise ValueError("Insufficient funds after lock")

            # 4. Create a transaction record
            transaction = Transaction.objects.create(
                wallet=wallet_to_debit,
                amount=amount,
                transaction_type='purchase',
                status='pending',
                reference=reference,
                idempotency_key=idempotency_key,
                transaction_id=f"TXN-{uuid.uuid4().hex}"
            )

            print("\n\nTransaction record created, proceeding to charge the wallet")

            # 5. Debit the wallet
            attempt_to_charge = charge_wallet(wallet_to_debit.wallet_id, float(amount), idempotency_key)

            print(f"\n\nCharge attempt response: {attempt_to_charge}\n\n")

            if attempt_to_charge.get("status") != "success":
                transaction.status = 'failed'
                transaction.save()
                raise ValueError("Failed to charge the wallet")

            wallet_to_debit.available_balance -= amount
            wallet_to_debit.save()

            # 6. Update the transaction status to successful
            transaction.status = 'successful'
            transaction.save()

            return transaction

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
