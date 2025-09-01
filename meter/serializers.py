from rest_framework import serializers
from .models import Meter
from .utils import add_meter_to_service

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

    def create(self, validated_data):
        user = self.context['request'].user
        organization = self.context['organization']

        validated_data['added_by'] = user
        validated_data['organization'] = organization

        meter_number = validated_data.get('meter_number')

        # Check if meter with the same number already exists for this organization
        if Meter.objects.filter(meter_number=meter_number, organization=organization).exists():
            raise serializers.ValidationError(
                {"meter_number": f"A meter with number '{meter_number}' already exists in your organization."}
            )

        try:
            response_data = add_meter_to_service(meter_number)
            
            response = response_data.get('response', {})
            status = response.get('status')
            message = response.get('message')

            if status == 'success':
                # "Meter already exists" is considered a success by the remote service
                # We can proceed to create it in our system if it doesn't exist
                instance = super().create(validated_data)
                return instance
            else:
                # Handle failure cases
                raise serializers.ValidationError({"detail": f"Failed to add meter: {message}"})

        except Exception as e:
            raise serializers.ValidationError({"detail": str(e)})