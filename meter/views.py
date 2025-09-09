from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from decimal import Decimal

from authentication.backends import APIKeyAuthentication
from authentication.models import Organization
from utils.permissions import IsOrganizationMember, IsOrganizationMemberOrAPIToken, IsReadOnlyOrAdmin
from .models import Meter, UtilityCost
from .serializers import MeterSerializer, UtilityCostSerializer
from .token_serializers import GenerateTokenSerializer
from .utils import generate_meter_token
# from wallet.utils import charge_organization_wallet
from wallet.models import Wallet
from wallet.services import ChargeService

class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['organization'] = Organization.objects.get(uuid=self.kwargs['org_uuid'])
        return context


class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'meter_uuid'

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])


class GenerateMeterTokenView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMemberOrAPIToken]
    authentication_classes = [APIKeyAuthentication, JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = GenerateTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        token_type = validated_data.get('token_type')
        meter_number = validated_data.get('meter_number')
        idempotency_key = request.headers.get('Idempotency-Key')
        org_uuid = self.kwargs['org_uuid']

        if not idempotency_key:
            return Response({"detail": "Idempotency-Key header is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            utility_cost = UtilityCost.objects.get(name=token_type)
        except UtilityCost.DoesNotExist:
            raise serializers.ValidationError(f"Cost for token type '{token_type}' is not configured.")

        try:
            organization = Organization.objects.get(uuid=org_uuid)
            wallet = Wallet.objects.get(reference=organization)
        except (Organization.DoesNotExist, Wallet.DoesNotExist):
            return Response({"detail": "Organization or wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        amount_to_charge = 0
        if token_type == 'credit':
            if 'utility_units' in validated_data:
                amount = validated_data['utility_units'] * utility_cost.cost
                validated_data['amount'] = Decimal(amount)
                if amount < utility_cost.cost:
                    raise serializers.ValidationError(f"Amount for credit token cannot be less than the cost of 1 unit ({utility_cost.cost}).")
                amount_to_charge = amount
            else:
                amount = Decimal(validated_data.get('amount'))
                if amount < utility_cost.cost:
                    raise serializers.ValidationError(f"Amount for credit token cannot be less than the cost of 1 unit ({utility_cost.cost}).")
                amount_to_charge = amount
        else:
            amount_to_charge = utility_cost.cost

        try:
            # Debit the wallet using the ChargeService
            transaction = ChargeService.debit_wallet(
                wallet_id=wallet.uuid,
                amount=amount_to_charge,
                reference=meter_number,
                idempotency_key=idempotency_key
            )

            if transaction.status != 'successful':
                return Response({"detail": "Transaction failed or is a duplicate request."}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            # Handle insufficient funds and other value errors from ChargeService
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # If token generation fails, refund the transaction
            if 'transaction' in locals() and transaction.status == 'successful':
                ChargeService.refund_wallet(transaction)
            
            return Response({"detail": f"An error occurred during token generation: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        try:
            response_data = generate_meter_token(token_type, validated_data)

            # charge_organization_wallet(organization, amount_to_charge, 'debit')

            # Process the response based on token type
            if token_type == 'kct':
                processed_response = [
                    {"description": item.get("description"), "token": item.get("tokenDec")}
                    for item in response_data.get('data', {}).get('data', [])
                ]
            elif token_type in ['credit', 'clear_credit', 'clear_tamper']:
                # Ensure data is not empty before accessing index 0
                data_list = response_data.get('data', {}).get('data', [])
                if data_list:
                    processed_response = {"token": data_list[0].get("tokenDec")}
                else:
                    processed_response = {"token": None}
            else:
                processed_response = response_data

            return Response(processed_response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UtilityCostListCreateView(generics.ListCreateAPIView):
    serializer_class = UtilityCostSerializer
    permission_classes = [IsReadOnlyOrAdmin]

    def get_queryset(self):
        return UtilityCost.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UtilityCostUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UtilityCostSerializer
    permission_classes = [IsReadOnlyOrAdmin]
    lookup_field = "uuid"

    def get_queryset(self):
        return UtilityCost.objects.filter(uuid=self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
