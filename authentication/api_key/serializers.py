# serializers.py - Add these to your existing serializers.py

from rest_framework import serializers
from .models import APIKey


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API keys (without exposing the actual key)"""
    
    key_type_display = serializers.CharField(source='get_key_type_display', read_only=True)
    scopes = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = [
            'uuid', 'key_id', 'key_type', 'key_type_display',
            'name', 'is_active', 'created_at', 'last_used_at', 'scopes'
        ]
        read_only_fields = ['uuid', 'key_id', 'created_at', 'last_used_at']
    
    def get_scopes(self, obj):
        return obj.get_scopes()


class CreateAPIKeySerializer(serializers.Serializer):
    """Serializer for creating new API keys"""
    
    key_type = serializers.ChoiceField(choices=APIKey.KEY_TYPES)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_key_type(self, value):
        # Check if organization already has this key type
        organization = self.context['organization']
        if APIKey.objects.filter(organization=organization, key_type=value).exists():
            raise serializers.ValidationError(
                f'Organization already has a {dict(APIKey.KEY_TYPES)[value]}'
            )
        return value


class APIKeyResponseSerializer(serializers.ModelSerializer):
    """Serializer for API key creation response (includes the actual key)"""
    
    full_key = serializers.CharField(read_only=True)
    key_type_display = serializers.CharField(source='get_key_type_display', read_only=True)
    scopes = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = [
            'uuid', 'key_id', 'full_key', 'key_type', 'key_type_display',
            'name', 'is_active', 'created_at', 'scopes'
        ]
    
    def get_scopes(self, obj):
        return obj.get_scopes()


# views.py - Add these views to handle API key management
