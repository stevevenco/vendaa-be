import abc
from datetime import datetime
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction


from .models import Wallet, Transaction
from authentication.models import Organization, User
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
    def get_wallet_transaction(self, wallet: Wallet, org_currency: str, month: int = None):
        pass

    @abc.abstractmethod
    def get_transaction_details(self, wallet: Wallet, transaction_id: str, org_currency):
        pass

    @abc.abstractmethod
    def create_shared_wallet(self, organization: Organization):
        pass

    @abc.abstractmethod
    def get_wallet_object(self, organization: Organization):
        pass


class SharedWalletService(WalletService):
    def create_wallet(self, organization: Organization):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def top_up_wallet(self, wallet: Wallet, amount: Decimal):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def refund_wallet(self, original_transaction: Transaction):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def get_wallet_balance(self, wallet: Wallet):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def get_wallet_transaction(self, wallet: Wallet, org_currency: str, month: int = None):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def get_transaction_details(self, wallet: Wallet, transaction_id: str, org_currency):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def get_wallet_object(self, organization: Organization):
        raise NotImplementedError("Shared wallet service does not support this operation.")

    def create_shared_wallet(self, organization: Organization):
        errors = []

        try:
            print(f"\nCreating production wallet for organization {organization.uuid}\n")
            ProductionWalletService().create_wallet(organization)
        except Exception as e:
            errors.append(f"Production wallet creation failed: {e}")

        try:
            print(f"\nCreating sandbox wallet for organization {organization.uuid}\n")
            SandboxWalletService().create_wallet(organization)
        except Exception as e:
            errors.append(f"Sandbox wallet creation failed: {e}")

        if errors:
            # You could log them instead of raising if you don’t want to break org creation
            print("\n".join(errors))


class ProductionWalletService(WalletService):
    def __init__(self):
        self.client = MeterServicesClient()

    def get_wallet_object(self, organization: Organization):
        wallet = Wallet.objects.filter(reference=organization, is_sandbox=False).first()
        if not wallet:
            raise ValueError("Wallet does not exist for this organization.")
        return wallet

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
                    "is_sandbox": False,
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
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status="success", is_sandbox=False).exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type="purchase",
            status="pending",
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}",
            is_sandbox=False,
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

            transaction.status = "success"
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
                status="success",
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}",
                is_sandbox=False,
            )

            wallet.available_balance += original_transaction.amount
            wallet.save()

            original_transaction.status = "refunded"
            original_transaction.save()

            return refund_transaction

    def get_wallet_balance(self, wallet: Wallet):
        status, response_data = self.client.get_balance(wallet.wallet_id)
        print(f"\n\nWallet balance response: {response_data}\n\n")
        if status == 200 and response_data.get("status") == "success":
            balance_data = response_data["data"]
            return balance_data["avail_balance_cur"]

        raise Exception("Failed to get wallet balance: " + str(response_data))

    
    def get_wallet_transaction(self, wallet: Wallet, org_currency: str, month=None):
        status, response_data = self.client.get_transactions(wallet.wallet_id, org_currency)
        if status == 200 and response_data.get('status') == 'success':
            if response_data['data'] is None:
                return []
            res_data = response_data['data']
            serializer_data = []

            for txn in res_data:
                # Parse created_at into datetime
                created_at_dt = datetime.strptime(txn['creation_date'], "%Y-%m-%d %H:%M:%S.%f")

                # If month filter is provided, skip transactions not in that month
                print(f"\n===Transaction date: {created_at_dt.month}, Filter month: {month}===\n")
                print(f"\n===Transaction date comparison: {created_at_dt.month != month}===, Type: {type(created_at_dt.month)} != {type(month)}===\n")
                if month and created_at_dt.month != int(month):
                    print(f"\nSkipping transaction: {txn['transaction_id']} from month {created_at_dt.month}\n")
                    continue

                txn_body = {
                    'title': txn['title'],
                    'transaction_id': txn['transaction_id'],
                    'amount': org_currency + f"{float(txn['amount']):.2f}",
                    'created_at': txn['creation_date'],
                    'status': txn['status'],
                    'event': txn['event'],
                }
                serializer_data.append(txn_body)
                print(f"\nIncluded transaction: {txn['transaction_id']} from month {created_at_dt.month}\n")

            return serializer_data

        raise Exception('Failed to fetch transactions: ' + str(response_data))

    def get_transaction_details(self, wallet: Wallet, transaction_id: str, org_currency: str):
        status, response_data = self.client.get_single_transaction(transaction_id)
        if status == 200 and response_data.get('status') == 'success':
            txn = response_data['data']
            txn_body = {
                'title': txn.get('title', f"Transaction {txn['transaction_id']}"),
                'transaction_id': txn['transaction_id'],
                'amount': org_currency + f"{float(txn['amount']):.2f}",
                'created_at': txn['creation_date'],
                'status': txn['status'],
                'event': txn['event'],
            }
            return txn_body

        return None

    def create_shared_wallet(self, organization: Organization):
        raise NotImplementedError("Production wallet service does not support this operation.")



class SandboxWalletService(WalletService):
    def get_wallet_object(self, organization):
        wallet = Wallet.objects.filter(reference=organization, is_sandbox=True).first()
        if not wallet:
            raise ValueError("Sandbox wallet does not exist for this organization.")
        return wallet

    def create_wallet(self, organization: Organization):
        amount = Decimal("100000.00")
        wallet, created = Wallet.objects.get_or_create(
            reference=organization,
            is_sandbox=True,
            defaults={
                "wallet_id": f"sandbox_{uuid.uuid4().hex}",
                "created_by": "sandbox@system.com",
                "currency": organization.currency or "NGN",
                "available_balance": amount,
                "ledger_balance": amount,
                "is_sandbox": True,
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
            status="success",
            reference=f"SANDBOX-FUND-{uuid.uuid4().hex}",
            transaction_id=f"TXN-FUND-{uuid.uuid4().hex}",
            is_sandbox=True,
        )
        return wallet

    def debit_wallet(self, wallet: Wallet, amount: Decimal, reference: str, idempotency_key: str = None):
        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key, status="success", is_sandbox=True).exists():
            raise ValueError("Duplicate request: A successful transaction with this idempotency key already exists.")

        transaction = Transaction.objects.create(
            title="Token Vend",
            event="Charge",
            wallet=wallet,
            amount=amount,
            transaction_type="purchase",
            status="pending",
            reference=reference,
            idempotency_key=idempotency_key,
            transaction_id=f"TXN-{uuid.uuid4().hex}",
            is_sandbox=True,
        )

        if wallet.available_balance < amount:
            transaction.status = "failed"
            transaction.save()
            raise InsufficientBalanceError("Insufficient balance in sandbox wallet")

        wallet.available_balance -= amount
        wallet.save()

        transaction.status = "success"
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
                status="success",
                reference=f"SANDBOX-FUND-{uuid.uuid4().hex}",
                transaction_id=f"TXN-FUND-{uuid.uuid4().hex}",
                is_sandbox=True,
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
                status="success",
                reference=original_transaction.transaction_id,
                transaction_id=f"TXN-REF-{uuid.uuid4().hex}",
                is_sandbox=True,
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

        print(f"\n\nSandbox wallet balance: {wallet.available_balance} {currency_symbol}\n\n")
        return f"{currency_symbol} {wallet.available_balance}"

    def get_wallet_transaction(self, wallet: Wallet, org_currency: str, month=None):
        transactions = Transaction.objects.filter(wallet=wallet, is_sandbox=True)
        if month:
            transactions = transactions.filter(created__month=month)
        transactions = transactions.order_by('-created')
        print(f"\n\n Sandbox transactions: {len(transactions)}")
        return transactions

    def get_transaction_details(self, wallet: Wallet, transaction_id: str, org_currency: str):
        transaction = Transaction.objects.filter(wallet=wallet, transaction_id=transaction_id, is_sandbox=True).first()
        if not transaction:
            return None
        return transaction

    def create_shared_wallet(self, organization: Organization):
        raise NotImplementedError("Sandbox wallet service does not support this operation.")


def get_wallet_service(organization: Organization, user: User):
    if user.display_state == 'test':
        print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
        return SandboxWalletService()
    print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
    return ProductionWalletService()
    # if organization.is_sandbox:
    #     print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
    #     return SandboxWalletService()
    # print(f"\nOrganization is sandbox routing to wallet sandbox service\n")
    # return ProductionWalletService()
