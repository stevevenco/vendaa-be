# models.py - Add these models to your existing models file

import secrets
import hashlib
from django.db import models
from django.core.exceptions import ValidationError

from config import settings
from utils.models import TrackObjectStateMixin


class APIKey(TrackObjectStateMixin):
    """
    API Key model for organization-scoped access control
    """
    KEY_TYPES = (
        ('secret', 'Secret Key'),
        ('public', 'Public Key'),
    )

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    key_type = models.CharField(max_length=10, choices=KEY_TYPES)
    key_id = models.CharField(max_length=50, unique=True)  # The public part (pk-... or sk-...)
    key_hash = models.CharField(max_length=128)  # Hashed version of the full key
    name = models.CharField(max_length=255, blank=True, null=True)  # Optional friendly name
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_keys'
    )

    class Meta:
        unique_together = ('organization', 'key_type')  # One key per type per org
        indexes = [
            models.Index(fields=['key_id']),
            models.Index(fields=['organization', 'key_type']),
        ]

    def clean(self):
        """Ensure only one key per type per organization"""
        if self.pk:
            # If updating existing key, exclude self from the check
            existing = APIKey.objects.filter(
                organization=self.organization,
                key_type=self.key_type
            ).exclude(pk=self.pk)
        else:
            existing = APIKey.objects.filter(
                organization=self.organization,
                key_type=self.key_type
            )
        
        if existing.exists():
            raise ValidationError(
                f'Organization already has a {self.get_key_type_display()}'
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_key_pair(cls):
        """Generate a new API key pair (public ID and secret)"""
        # Generate random bytes
        key_bytes = secrets.token_bytes(32)
        key_string = secrets.token_urlsafe(32)
        
        return key_string, key_bytes
    
    @classmethod
    def create_api_key(cls, organization, key_type, created_by=None, name=None):
        """Create a new API key for an organization"""
        
        # Check if key already exists
        if cls.objects.filter(organization=organization, key_type=key_type).exists():
            raise ValidationError(f'Organization already has a {key_type} key')
        
        # Generate key
        key_string, key_bytes = cls.generate_key_pair()
        
        # Create key ID with appropriate prefix
        prefix = 'sk-' if key_type == 'secret' else 'pk-'
        key_id = f"{prefix}{secrets.token_urlsafe(16)}"
        
        # Hash the full key for storage
        full_key = f"{key_id}.{key_string}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Create the API key record
        api_key = cls.objects.create(
            organization=organization,
            key_type=key_type,
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_by=created_by
        )
        
        return api_key, full_key
    
    @classmethod
    def validate_key(cls, full_key):
        """Validate an API key and return the associated APIKey instance"""
        try:
            # Split key into ID and secret parts
            if '.' not in full_key:
                return None
                
            key_id, _ = full_key.split('.', 1)
            
            # Hash the full key
            key_hash = hashlib.sha256(full_key.encode()).hexdigest()
            
            # Find matching key
            api_key = cls.objects.select_related('organization').get(
                key_id=key_id,
                key_hash=key_hash,
                is_active=True
            )
            
            # Update last used timestamp
            from django.utils import timezone
            api_key.last_used_at = timezone.now()
            api_key.save(update_fields=['last_used_at'])
            
            return api_key
            
        except (cls.DoesNotExist, ValueError):
            return None
    
    def get_scopes(self):
        """Return the scopes available for this key type"""
        if self.key_type == 'secret':
            return [
                'auth:read',
                'organizations:full',
                'invitations:full', 
                'wallet:full',
                'meters:full',
                'apikeys:full',
                'token_purchase:create'
            ]
        elif self.key_type == 'public':
            return [
                'meters:read',
                'organizations:read'
            ]
        return []
    
    def has_scope(self, required_scope):
        """Check if this key has the required scope"""
        scopes = self.get_scopes()
        
        # Parse required scope
        resource, action = required_scope.split(':')
        
        # Check for exact match
        if required_scope in scopes:
            return True
            
        # Check for 'full' access to resource
        if f"{resource}:full" in scopes:
            return True
            
        return False
    
    def __str__(self):
        return f"{self.get_key_type_display()} for {self.organization.name} ({self.key_id})"


