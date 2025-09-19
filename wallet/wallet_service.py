import abc
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction


from .models import Wallet, Transaction
from authentication.models import Organization
from countries.models import Country
from .meter_services_client import MeterServicesClient


class InsufficientBalanceError(Exception):
    def __init__(self, message="Insufficient balance", available_balance=None):
        self.message = message
        self.available_balance = available_balance
        super().__init__(self.message)


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

    @abc.abstractmethod
    def get_wallet_balance(self, wallet: Wallet):
        pass

    @abc.abstractmethod
    def get_wallet_transaction(self, wallet: Wallet, org_currency: str):
        pass


class ProductionWalletService(WalletService):
    def __init__(self):
        self.client = MeterServicesClient()

    def create_wallet(self, organization: Organization):
        status, response_data = self.client.create_wallet(
            party_name=organization.name,
            reference=organization.uuid,
            currency=organization.currency,
        )

        if status == 200 and response_data.get("status") == "success":
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

        if status == 400:
            error_message = str(response_data)
            if "Duplicate entry" in error_message or "IntegrityError" in error_message:
                # could call self.client.get_wallets() here and sync
                raise Exception("Wallet already exists on the service.")

        raise Exception("Failed to create wallet: " + str(response_data))

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status="Success").exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type="purchase",
            status="pending",
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}"
        )

        try:
            status, response_data = self.client.charge_wallet(
                debit_party=wallet.wallet_id,
                credit_party=settings.CREDIT_WALLET_ID,
                amount=amount,
                debit_party_reference=wallet.reference.uuid,
            )

            if status != 200 or response_data.get("status") != "success":
                err_type = response_data.get("data", {}).get("err_type")
                if err_type == "insufficient-balance":
                    raise InsufficientBalanceError(message=response_data.get("message"))
                raise ValueError(f"Failed to charge wallet: {response_data.get('message')}")

            wallet.available_balance -= amount
            wallet.save()

            transaction.status = "successful"
            transaction.save()

            return transaction

        except Exception as e:
            transaction.status = "failed"
            transaction.save()
            raise e

    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        status, response_data = self.client.initiate_payment(wallet.wallet_id, amount, settings.FRONTEND_URL)
        if status == 200 and response_data.get("status") == "success":
            return response_data["data"]["payment_options"]

        raise Exception("Failed to initiate payment: " + str(response_data))

    def refund_wallet(self, original_transaction: Transaction):
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(uuid=original_transaction.wallet.uuid)

            if Transaction.objects.filter(reference=original_transaction.transaction_id, transaction_type="refund").exists():
                return

            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                amount=original_transaction.amount,
                transaction_type="refund",
                status="Success",
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}"
            )

            wallet.available_balance += original_transaction.amount
            wallet.save()

            original_transaction.status = "refunded"
            original_transaction.save()

            return refund_transaction

    def get_wallet_balance(self, wallet: Wallet):
        status, response_data = self.client.get_balance(wallet.wallet_id)
        if status == 200 and response_data.get("status") == "success":
            balance_data = response_data["data"]
            return balance_data["avail_balance_cur"]

        raise Exception("Failed to get wallet balance: " + str(response_data))

    def get_wallet_transaction(self, wallet: Wallet, org_currency: str):
        status, response_data = self.client.get_transactions(wallet.wallet_id, org_currency)
        if status == 200 and response_data.get('status') == 'success':
            res_data = response_data['data']
            # print(f"\n\nres_data: {res_data}\n\n")
            # return [TransactionSerializer(txn).data for txn in res_data]
            serializer_data = []
            for txn in res_data:
                txn_body = {}
                txn_body['title'] = txn['title']
                txn_body['transaction_id'] = txn['transaction_id']
                txn_body['amount'] = org_currency + f"{float(txn['amount']):.2f}"
                txn_body['created_at'] = txn['creation_date']
                txn_body['status'] = txn['status']
                txn_body['event'] = txn['event']
                print(f"\n\n Transaction: {txn_body}\n\n")
                serializer_data.append(txn_body)
            print(f"\n\n Transaction serialized data: {serializer_data[:3]}")
            return serializer_data

        raise Exception('Failed to fetch transactions: ' + str(response_data))



class SandboxWalletService(WalletService):
    def create_wallet(self, organization: Organization):
        amount = Decimal("100000.00")
        wallet, created = Wallet.objects.get_or_create(
            reference=organization,
            defaults={
                "wallet_id": f"sandbox_{uuid.uuid4().hex}",
                "created_by": "sandbox@system.com",
                "currency": organization.currency or "NGN",
                "available_balance": amount,
                "ledger_balance": amount,
            }
        )
        if not created and wallet.available_balance == 0:
            wallet.available_balance = amount
            wallet.ledger_balance = amount
            wallet.save()

        Transaction.objects.create(
            title="Auto Top-Up",
            wallet=wallet,
            amount=amount,
            event="Fund",
            transaction_type="funding",
            status="Success",
            reference=f"SANDBOX-FUND-{uuid.uuid4().hex}",
            transaction_id=f"TXN-FUND-{uuid.uuid4().hex}"
        )
        return wallet

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status="Success").exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            title="Debit",
            event="Charge",
            wallet=wallet,
            amount=amount,
            transaction_type="purchase",
            status="pending",
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}"
        )

        if wallet.available_balance < amount:
            transaction.status = "failed"
            transaction.save()
            raise InsufficientBalanceError("Insufficient balance in sandbox wallet")

        wallet.available_balance -= amount
        wallet.save()

        transaction.status = "successful"
        transaction.save()

        return transaction

    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        with db_transaction.atomic():
            wallet.available_balance += Decimal(amount)
            wallet.save()

            Transaction.objects.create(
                title="Wallet Top-Up",
                event="Fund",
                wallet=wallet,
                amount=amount,
                transaction_type="funding",
                status="Success",
                reference=f"SANDBOX-FUND-{uuid.uuid4().hex}",
                transaction_id=f"TXN-FUND-{uuid.uuid4().hex}"
            )

        return {"status": "success", "message": "Sandbox wallet topped up successfully."}

    def refund_wallet(self, original_transaction: Transaction):
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(uuid=original_transaction.wallet.uuid)

            if Transaction.objects.filter(reference=original_transaction.transaction_id, transaction_type="refund").exists():
                return

            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                amount=original_transaction.amount,
                transaction_type="refund",
                status="Success",
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}"
            )

            wallet.available_balance += original_transaction.amount
            wallet.save()

            original_transaction.status = "refunded"
            original_transaction.save()

            return refund_transaction

    def get_wallet_balance(self, wallet: Wallet) -> str:
        country = wallet.reference.country
        if not country:
            currency_symbol = wallet.reference.currency or ""
        else:
            currency_symbol = country.currency_symbol

        return f"{currency_symbol} {wallet.available_balance}"

    def get_wallet_transaction(self, wallet: Wallet, org_currency: str):
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created')
        print(f"\n\n Sandbox transactions: {len(transactions)}")
        return transactions


def get_wallet_service(organization: Organization):
    if organization.is_sandbox:
        print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
        return SandboxWalletService()
    print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
    return ProductionWalletService()
