from rest_framework import serializers

class BaseTokenSerializer(serializers.Serializer):
    TOKEN_TYPES = [
        ('kct', 'KCT'),
        ('credit', 'Credit'),
        ('mse', 'MSE'),
        ('test', 'Test'),
        ('ditk', 'DITK'),
    ]
    token_type = serializers.ChoiceField(choices=TOKEN_TYPES)
    meter_number = serializers.CharField()
    ea = serializers.IntegerField(required=False)
    tct = serializers.IntegerField(required=False)
    sgc = serializers.IntegerField(required=False)
    krn = serializers.IntegerField(required=False)
    ti = serializers.IntegerField(required=False)
    allow_krn_update = serializers.BooleanField(required=False)
    key_expiry_number = serializers.IntegerField(required=False)
    use3kct = serializers.BooleanField(required=False)
    allow_ken_update = serializers.BooleanField(required=False)


class KCTTokenSerializer(BaseTokenSerializer):
    meter_number = serializers.CharField()
    token_type = serializers.CharField()
    amount = serializers.IntegerField()


class CreditTokenSerializer(BaseTokenSerializer):
    meter_number = serializers.CharField()
    token_type = serializers.CharField()
    amount = serializers.IntegerField()


class ClearCreditTokenSerializer(BaseTokenSerializer):
    meter_number = serializers.CharField()
    token_type = serializers.CharField()
    amount = serializers.IntegerField()


class ClearTamperTokenSerializer(BaseTokenSerializer):
    meter_number = serializers.CharField()
    token_type = serializers.CharField()
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value >= 1:
            raise serializers.ValidationError("Amount must be lower than 1.")
        return value


class MSETokenSerializer(BaseTokenSerializer):
    subclass = serializers.IntegerField()
    amount = serializers.IntegerField()


class GenerateTokenSerializer(serializers.Serializer):
    token_type = serializers.ChoiceField(choices=BaseTokenSerializer.TOKEN_TYPES)

    def to_internal_value(self, data):
        token_type = data.get('token_type')
        if token_type == 'kct':
            serializer = KCTTokenSerializer(data=data)
        elif token_type == 'credit':
            serializer = CreditTokenSerializer(data=data)
        elif token_type == 'clear_credit':
            serializer = ClearCreditTokenSerializer(data=data)
        elif token_type == 'clear_tamper':
            serializer = ClearTamperTokenSerializer(data=data)
        elif token_type == 'mse':
            serializer = MSETokenSerializer(data=data)
        else:
            # For 'test' and 'ditk', we can use the base serializer if they don't have extra required fields
            # or create specific serializers if they do. For now, we'll just validate the base fields.
            serializer = BaseTokenSerializer(data=data)
        
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
