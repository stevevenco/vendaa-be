import uuid
from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction as db_transaction
from decimal import Decimal

from authentication.api_key.authentication import APIKeyAuthentication
from authentication.api_key.permissions import IsOrganizationMemberOrAPIKey, MetersFullPermission, MetersReadPermission
from authentication.models import Organization
from utils.permissions import IsOrganizationMember, IsReadOnlyOrAdmin
from .models import Meter, UtilityCost, UtilityVend
from .serializers import MeterSerializer, UtilityCostSerializer
from .token_serializers import GenerateTokenSerializer
from .utils import generate_meter_token
from wallet.models import Wallet
from wallet.services import ChargeService, InsufficientBalanceError

# class MeterListCreateView(generics.ListCreateAPIView):
#     serializer_class = MeterSerializer
#     permission_classes = [IsAuthenticated, IsOrganizationMember]

#     def get_queryset(self):
#         return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['request'] = self.request
#         context['organization'] = Organization.objects.get(uuid=self.kwargs['org_uuid'])
#         return context
    

class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer
    authentication_classes = [APIKeyAuthentication, JWTAuthentication]
    
    def get_permissions(self):
        """Dynamic permissions based on request method and authentication"""
        if self.request.method == 'GET':
            # Read-only access for both public and secret keys
            permission_classes = [IsAuthenticated, MetersReadPermission, IsOrganizationMemberOrAPIKey]
        else:
            # Write access only for secret keys and JWT users
            permission_classes = [IsAuthenticated, MetersFullPermission, IsOrganizationMemberOrAPIKey]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['organization'] = Organization.objects.get(uuid=self.kwargs['org_uuid'])
        return context


class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer
    authentication_classes = [APIKeyAuthentication, JWTAuthentication]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'meter_uuid'
    
    def get_permissions(self):
        """Dynamic permissions based on request method"""
        if self.request.method == 'GET':
            # Read access for both public and secret keys
            permission_classes = [IsAuthenticated, MetersReadPermission, IsOrganizationMemberOrAPIKey]
        else:
            # Write/Delete access only for secret keys and JWT users
            permission_classes = [IsAuthenticated, MetersFullPermission, IsOrganizationMemberOrAPIKey]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])


class GenerateMeterTokenView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

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
            organization = Organization.objects.get(uuid=org_uuid)
            wallet = Wallet.objects.get(reference=organization)
            meter = Meter.objects.get(meter_number=meter_number, organization=organization)
        except (UtilityCost.DoesNotExist, Organization.DoesNotExist, Wallet.DoesNotExist, Meter.DoesNotExist) as e:
            return Response({"detail": f"Configuration or entity not found: {e}"}, status=status.HTTP_404_NOT_FOUND)

        amount_to_charge = utility_cost.cost
        try:
            if token_type == 'credit':
                utility_units = validated_data.get('utility_units')
            if utility_units:
                amount = Decimal(utility_units) * utility_cost.cost
            else: amount = Decimal(validated_data.get('amount'))
            if amount < utility_cost.cost:
                raise serializers.ValidationError(f"Amount for credit token must be at least {utility_cost.cost}.")
            amount_to_charge = amount
        except UtilityCost.DoesNotExist:
            return Response({"detail": f"Utility cost configuration for '{token_type}' not found."}, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_transaction.atomic():
                # Lock wallet for update
                locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

                # Create a utility vend record
                utility_vend = UtilityVend.objects.create(
                    meter=meter,
                    amount=amount_to_charge,
                    utility_cost=utility_cost,
                    vend_reference=f"VEND-{uuid.uuid4().hex}",
                    initiated_by=request.user,
                    status='pending'
                )

                # 1. Generate the token
                token_response = generate_meter_token(token_type, validated_data, meter)

                # 2. Charge the wallet
                transaction = ChargeService.debit_wallet(
                    wallet=locked_wallet,
                    amount=amount_to_charge,
                    reference=f"VEND-{meter.meter_number}-{utility_vend.uuid}",
                    idempotency_key=idempotency_key
                )
                utility_vend.transaction = transaction
                utility_vend.save()

                # Process response and save token
                if token_type == 'kct':
                    tokens = [item.get("tokenDec") for item in token_response.get('data', {}).get('data', [])]
                    utility_vend.token = ", ".join(tokens)
                    processed_response = [{"description": item.get("description"), "token": item.get("tokenDec")} for item in token_response.get('data', {}).get('data', [])]
                else:
                    data_list = token_response.get('data', {}).get('data', [])
                    token = data_list[0].get("tokenDec") if data_list else None
                    utility_vend.token = token
                    processed_response = {"token": token}

                utility_vend.token_details = token_response
                utility_vend.status = 'successful'
                utility_vend.save()

            return Response(processed_response, status=status.HTTP_200_OK)

        except InsufficientBalanceError as e:
            return Response({
                "detail": e.message,
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        except serializers.ValidationError as e:
            return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # The atomic transaction will roll back all DB changes
            return Response({"detail": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
