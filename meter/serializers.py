from rest_framework import serializers

from meter.utils import validate_meter_no
from .models import Meter, UtilityCost, UtilityVend
from .meter_service import get_meter_service

class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = [
            "uuid",
            "customer_name",
            "meter_number",
            "email",
            "phone",
            "address",
            "sgc",
            "tariff_index",
            "key_revision_number",
            "meter_type",
            "added_by",
            "organization",
            "created",
            "last_updated",
        ]
        read_only_fields = ["uuid", "added_by", "organization", "created", "last_updated"]

    # --- Field Validations ---
    def validate_meter_number(self, value):
        """
        Validate meter number
        """
        organization_is_sandbox = self.context['organization'].is_sandbox
        if not organization_is_sandbox:
            if not validate_meter_no(value):
                raise serializers.ValidationError("Incorrect meter number.")
        return value

    def validate_tariff_index(self, value):
        """
        TI (tariff_index) must be an integer between 1 and 99 (1 or 2 digits).
        """
        if not value.isdigit():
            raise serializers.ValidationError("Tariff Index must be numeric.")
        num = int(value)
        if num < 1 or num > 99:
            raise serializers.ValidationError("Tariff Index must be between 1 and 99.")
        return value

    def validate_key_revision_number(self, value):
        """
        KRN (key_revision_number) must be either 1 or 2.
        """
        if value not in ["1", "2"]:
            raise serializers.ValidationError("Key Revision Number must be either 1 or 2.")
        return value

    def validate_sgc(self, value):
        """
        SGC must be exactly 6 digits.
        """
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("SGC must be exactly 6 digits.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        organization = self.context['organization']

        validated_data['added_by'] = user
        validated_data['organization'] = organization

        meter_number = validated_data.get('meter_number')
        print(f"\n\nAttempting to add meter number {meter_number} to organization {organization.uuid}\n\n")

        # Check if meter with the same number already exists for this organization
        meter_service = get_meter_service(organization)
        meter = meter_service.get_meter_by_number(meter_number, organization=organization)
        print(f"\n\nChecked existence of meter number {meter_number} in organization {organization.uuid}, result: {meter}")
        if meter:
            print(f"\n\nMeter number {meter_number} already exists in organization {organization.uuid}")
            raise serializers.ValidationError(
                {"meter_number": f"A meter with number '{meter_number}' already exists in your organization."}
            )

        try:
            # meter_service = get_meter_service(organization)
            response_data = meter_service.add_meter(meter_number)
            print(f"\n\nMeter Service Response Data: {response_data}\n\n")

            response = response_data.get('response', {})
            status = response.get('status')
            message = response.get('message')

            if status == 'success':
                # Proceed with local creation
                instance = super().create(validated_data)
                return instance
            else:
                raise serializers.ValidationError({"detail": f"Failed to add meter: {message}"})

        except Exception as e:
            raise serializers.ValidationError({"detail": "Invalid meter number"})


class UtilityCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityCost
        fields = ["uuid", "name", "cost", "created", "last_updated"]
        read_only_fields = ["uuid", "created", "last_updated"]

    def validate_name(self, value):
        value = str(value).lower()
        if UtilityCost.objects.filter(name=value).exists():
            raise serializers.ValidationError("Utility cost with this name already exists.")
        return value


class UtilityVendsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UtilityVend
        fields = ['meter', 'created', 'amount', 'vend_reference']