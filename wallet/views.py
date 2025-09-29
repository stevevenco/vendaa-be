from decimal import Decimal
import json
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView

from django.shortcuts import get_object_or_404

from authentication.api_key.authentication import APIKeyAuthentication
from authentication.api_key.permissions import IsOrganizationMemberOrAPIKey, TransactionFullPermission, TransactionReadPermission, WalletFullPermission
from utils.permissions import HasOrgPermission

from .serializers import (
    SandboxTransactionSerializer, WalletCreateSerializer, WalletSerializer, WalletBalanceSerializer,
    PaymentOptionSerializer, TransactionSerializer
)
from .models import Wallet
from authentication.models import Organization
# from .meter_services_client import get_wallet_balance, initiate_wallet_payment, get_wallet_transaction_history
from .wallet_service import get_wallet_service

from utils.pagination import CustomPagination

class CreateWalletView(APIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        WalletFullPermission,
        HasOrgPermission('wallet', 'write')
    ]

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


class WalletBalanceView(APIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        WalletFullPermission,
        HasOrgPermission('wallet', 'read')
    ]

    def get(self, request, organization_id):
        # Get the wallet for this organization
        organization = get_object_or_404(Organization, uuid=organization_id)
        wallet_service = get_wallet_service(organization, request.user)
        wallet = wallet_service.get_wallet_object(organization)
        # wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        try:
            # Get current balance from meter services
            # organization = wallet.reference
            # wallet_service = get_wallet_service(organization)
            external_balance_str = wallet_service.get_wallet_balance(wallet)
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
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        WalletFullPermission,
        HasOrgPermission('wallet', 'write')
    ]

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
        organization = get_object_or_404(Organization, uuid=organization_id)
        wallet_service = get_wallet_service(organization, request.user)
        wallet = wallet_service.get_wallet_object(organization)
        # wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        try:
            # Get wallet service
            # organization = wallet.reference
            # wallet_service = get_wallet_service(organization)

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


class TransactionListView(ListAPIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
        TransactionReadPermission,
        HasOrgPermission('transaction', 'read'),
    ]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Return the queryset of transactions for the given organization.
        """
        organization_id = self.kwargs["organization_id"]

        # Get the wallet for this organization
        organization = get_object_or_404(Organization, uuid=organization_id)
        wallet_service = get_wallet_service(organization, self.request.user)
        wallet = wallet_service.get_wallet_object(organization)
        # wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        # Get organization + wallet service
        # organization = get_object_or_404(Organization, uuid=organization_id)
        currency = organization.currency
        month = self.request.query_params.get('month')
        print(f"\n===Filter month: {month}===\n")
        # wallet_service = get_wallet_service(organization)

        # Get transaction history from external service
        transactions = wallet_service.get_wallet_transaction(wallet, currency, month=month)

        # Store organization so we can use it later in serializer_class
        self.organization = organization

        return transactions

    def get_serializer_class(self):
        """
        Dynamically pick serializer depending on sandbox flag.
        """
        if self.request.user.display_state == 'test':
            return SandboxTransactionSerializer
        return TransactionSerializer
        # if self.organization.is_sandbox:
        #     return SandboxTransactionSerializer
        # return TransactionSerializer


class TransactionDetailView(RetrieveAPIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
        TransactionReadPermission,
        HasOrgPermission('transaction', 'read'),
    ]
    serializer_class = TransactionSerializer

    def get_object(self):
        """
        Return the transaction object for the given organization and transaction UUID.
        """
        organization_id = self.kwargs["organization_id"]
        print(f"\n===Organization ID: {organization_id}===\n")
        transaction_id = self.kwargs["transaction_id"]
        print(f"\n===Transaction ID: {transaction_id}===\n")

        # Get the wallet for this organization
        organization = get_object_or_404(Organization, uuid=organization_id)
        wallet_service = get_wallet_service(organization, self.request.user)
        wallet = wallet_service.get_wallet_object(organization)
        # wallet = get_object_or_404(Wallet, reference__uuid=organization_id)

        # Get organization + wallet service
        # organization = get_object_or_404(Organization, uuid=organization_id)
        currency = organization.currency

        # Get transaction details from external service
        transaction = wallet_service.get_transaction_details(wallet, transaction_id, currency)
        print(f"\n===Transaction: {transaction}===\n")

        if not transaction:
            raise serializers.ValidationError(
                f"Transaction with ID '{transaction_id}' not found in your organization."
            )

        # Store organization so we can use it later in serializer_class
        self.organization = organization

        return transaction

    def get_serializer_class(self):
        """
        Dynamically pick serializer depending on sandbox flag.
        """
        if self.request.user.display_state == 'test':
            return SandboxTransactionSerializer
        return TransactionSerializer