from decimal import Decimal
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.shortcuts import get_object_or_404

from authentication.api_key.authentication import APIKeyAuthentication
from authentication.api_key.permissions import IsOrganizationMemberOrAPIKey, WalletFullPermission

from .serializers import (
    WalletCreateSerializer, WalletSerializer, WalletBalanceSerializer,
    PaymentOptionSerializer, TransactionSerializer
)
from .models import Wallet
from authentication.models import Organization
from .utils import get_wallet_balance, initiate_wallet_payment, get_wallet_transaction_history
from .wallet_service import get_wallet_service

class CreateWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletCreateSerializer(data=request.data)
        if serializer.is_valid():
            wallet = serializer.save()
            response_serializer = WalletSerializer(wallet)
            return Response({
                'message': 'Wallet created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class WalletBalanceView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, organization_id):
#         # Get the wallet for this organization
#         wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

#         try:
#             # Get current balance from meter services
#             external_balance_str = get_wallet_balance(wallet.wallet_id)
#             currency_symbol = external_balance_str.split()[0]

#             # Clean up the balance string to decimal for comparison
#             cleaned_balance = external_balance_str.replace(currency_symbol, '').replace(',', '').strip()
#             balance_decimal = Decimal(cleaned_balance)

#             # Update wallet if external balance is different
#             if balance_decimal != wallet.available_balance:
#                 wallet.available_balance = balance_decimal
#                 wallet.save()

#             serializer = WalletBalanceSerializer({
#                 'available_balance': f"{currency_symbol}{wallet.available_balance:,.2f}",
#                 'ledger_balance': f"{currency_symbol}{wallet.ledger_balance:,.2f}",
#                 'wallet_id': wallet.wallet_id,
#                 'currency': wallet.currency
#             })
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class WalletBalanceView(APIView):
    authentication_classes = [APIKeyAuthentication, JWTAuthentication]
    permission_classes = [
        IsAuthenticated,
        WalletFullPermission,
        IsOrganizationMemberOrAPIKey
    ]
    
    def get(self, request, organization_id):
        # Get the wallet for this organization
        wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        try:
            # Get current balance from meter services
            external_balance_str = get_wallet_balance(wallet.wallet_id)
            currency_symbol = external_balance_str.split()[0]

            # Clean up the balance string to decimal for comparison
            cleaned_balance = external_balance_str.replace(currency_symbol, '').replace(',', '').strip()
            balance_decimal = Decimal(cleaned_balance)

            # Update wallet if external balance is different
            if balance_decimal != wallet.available_balance:
                wallet.available_balance = balance_decimal
                wallet.save()

            serializer = WalletBalanceSerializer({
                'available_balance': f"{currency_symbol}{wallet.available_balance:,.2f}",
                'ledger_balance': f"{currency_symbol}{wallet.ledger_balance:,.2f}",
                'wallet_id': wallet.wallet_id,
                'currency': wallet.currency
            })
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        # Validate payment option
        payment_option = request.query_params.get('payment_option')
        print(f"\n\npayment_option: {payment_option}\n\n")
        if payment_option not in ['online_checkout', 'bank_transfer']:
            return Response(
                {'error': 'Invalid payment option. Must be either online_checkout or bank_transfer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate amount
        try:
            amount = float(request.query_params.get('amount', 0))
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return Response(
                {'error': 'Amount must be a positive number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get wallet
        wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        try:
            # Get wallet service
            organization = wallet.reference
            wallet_service = get_wallet_service(organization)

            # Get payment options
            payment_options = wallet_service.top_up_wallet(wallet, amount)

            # Filter options based on payment type
            if payment_option == 'online_checkout':
                options = payment_options.get('card_options', [])
            else:  # bank_transfer
                options = payment_options.get('bank_options', [])

            # Serialize the options
            serializer = PaymentOptionSerializer(options, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# class TransactionListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, organization_id):
#         # Get the wallet for this organization
#         wallet = get_object_or_404(Wallet, reference__uuid=organization_id)
#         print(f"\n\nwallet: {wallet}\n\n")

#         try:
#             # Get transaction history from meter services
#             org_currency = Organization.objects.get(uuid=organization_id).currency
#             currency = org_currency if org_currency else "₦"
#             transactions = get_wallet_transaction_history(wallet.wallet_id, org_currency)
#             print(f"\n\ntransactions: {transactions}\n\n")

#             serializer_data = []
#             for txn in transactions:
#                 txn_body = {}
#                 txn_body['title'] = txn['title']
#                 txn_body['transaction_id'] = txn['transaction_id']
#                 txn_body['amount'] = currency + f"{float(txn['amount']):.2f}"
#                 txn_body['created_at'] = txn['creation_date']
#                 txn_body['status'] = txn['status']
#                 txn_body['event'] = txn['event']
#                 print(f"\n\n Transaction: {txn_body}\n\n")
#                 serializer_data.append(txn_body)
#                 # print(f"\n\ntxn_body: {txn_body}\n\n")

#             # Serialize the transactions
#             serializer = TransactionSerializer(serializer_data, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


class TransactionListView(APIView):
    authentication_classes = [APIKeyAuthentication, JWTAuthentication]
    permission_classes = [
        IsAuthenticated,
        WalletFullPermission,
        IsOrganizationMemberOrAPIKey
    ]

    def get(self, request, organization_id):
        # Get the wallet for this organization
        wallet = get_object_or_404(Wallet, reference__uuid=organization_id)
        print(f"\n\nwallet: {wallet}\n\n")

        try:
            # Get transaction history from meter services
            org_currency = Organization.objects.get(uuid=organization_id).currency
            currency = org_currency if org_currency else "₦"
            transactions = get_wallet_transaction_history(wallet.wallet_id, org_currency)
            print(f"\n\ntransactions: {transactions}\n\n")

            serializer_data = []
            for txn in transactions:
                txn_body = {}
                txn_body['title'] = txn['title']
                txn_body['transaction_id'] = txn['transaction_id']
                txn_body['amount'] = currency + f"{float(txn['amount']):.2f}"
                txn_body['created_at'] = txn['creation_date']
                txn_body['status'] = txn['status']
                txn_body['event'] = txn['event']
                print(f"\n\n Transaction: {txn_body}\n\n")
                serializer_data.append(txn_body)
                # print(f"\n\ntxn_body: {txn_body}\n\n")

            # Serialize the transactions
            serializer = TransactionSerializer(serializer_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


