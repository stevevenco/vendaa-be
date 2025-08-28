from rest_framework import serializers
import requests
from django.conf import settings

from authentication.models import Organization
from .models import Wallet

class WalletCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()

    def create(self, validated_data):
        from .utils import create_wallet_for_organization

        org = Organization.objects.get(uuid=validated_data['organization_id'])
        try:
            return create_wallet_for_organization(org)
        except Exception as e:
            raise serializers.ValidationError(str(e))

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['wallet_id', 'created_by', 'reference', 'currency', 'available_balance']
        read_only_fields = ['wallet_id', 'created_by', 'currency', 'available_balance']

class WalletBalanceSerializer(serializers.Serializer):
    balance = serializers.CharField()

class PaymentOptionSerializer(serializers.Serializer):
    payment_gateway = serializers.CharField()
    slug = serializers.CharField()
    logo = serializers.URLField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    fee = serializers.DecimalField(max_digits=20, decimal_places=2)
    provider = serializers.CharField(required=False)
    payment_url = serializers.URLField(required=False)
    bank_name = serializers.CharField(required=False)
    icon = serializers.URLField(required=False)
    account_number = serializers.CharField(required=False)
    account_name = serializers.CharField(required=False)
    account_reference = serializers.CharField(required=False)

