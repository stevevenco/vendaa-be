# Signal to automatically create API keys when organization is created
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from authentication.models import Organization
from .models import APIKey

@receiver(post_save, sender=Organization)
def create_organization_api_keys(sender, instance, created, **kwargs):
    """Automatically create API keys when organization is created"""
    if created:
        try:
            # Create secret key
            APIKey.create_api_key(
                organization=instance,
                key_type='secret',
                created_by=instance.created_by,
                name='Secret Key'
            )
            
            # Create public key  
            APIKey.create_api_key(
                organization=instance,
                key_type='public', 
                created_by=instance.created_by,
                name='Public Key'
            )
        except Exception as e:
            # Log error but don't fail organization creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create API keys for organization {instance.uuid}: {e}")