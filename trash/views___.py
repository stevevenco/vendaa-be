from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal

from authentication.models import Organization
from utils.permissions import IsOrganizationMember
from .models import Meter
from .serializers import MeterSerializer
from .token_serializers import GenerateTokenSerializer
from .utils import generate_meter_token
from wallet.models import Wallet
from wallet.old_services import ChargeService


class GenerateMeterTokenView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def post(self, request, *args, **kwargs):
        serializer = GenerateTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        amount = Decimal(validated_data.get('amount'))
        meter_number = validated_data.get('meter_number')
        idempotency_key = request.headers.get('Idempotency-Key')

        if not idempotency_key:
            return Response({"detail": "Idempotency-Key header is required."}, status=status.HTTP_400_BAD_REQUEST)

        org_uuid = self.kwargs['org_uuid']
        try:
            organization = Organization.objects.get(uuid=org_uuid)
            wallet = Wallet.objects.get(reference=organization)
        except (Organization.DoesNotExist, Wallet.DoesNotExist):
            return Response({"detail": "Organization or wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Debit the wallet using the ChargeService
            transaction = ChargeService.debit_wallet(
                wallet_id=wallet.pk,
                amount=amount,
                reference=meter_number,
                idempotency_key=idempotency_key
            )

            if transaction.status != 'successful':
                return Response({"detail": "Transaction failed or is a duplicate request."}, status=status.HTTP_400_BAD_REQUEST)

            # If the charge was successful, proceed to generate the token
            token_type = validated_data.get('token_type')
            response_data = generate_meter_token(token_type, validated_data)

            # Process the response based on token type
            if token_type == 'kct':
                processed_response = [
                    {"description": item.get("description"), "token": item.get("tokenDec")}
                    for item in response_data.get('data', {}).get('data', [])
                ]
            elif token_type in ['credit', 'clear_credit', 'clear_tamper']:
                data_list = response_data.get('data', {}).get('data', [])
                if data_list:
                    processed_response = {"token": data_list[0].get("tokenDec")}
                else:
                    processed_response = {"token": None}
            else:
                processed_response = response_data

            return Response(processed_response, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle insufficient funds and other value errors from ChargeService
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # If token generation fails, refund the transaction
            if 'transaction' in locals() and transaction.status == 'successful':
                ChargeService.refund_wallet(transaction)
            
            return Response({"detail": f"An error occurred during token generation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
