from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import Organization
from .services import SharedAPIKeyService

@receiver(post_save, sender=Organization)
def create_organization_api_keys(sender, instance, created, **kwargs):
    """
    Automatically create API keys for both live and sandbox environments
    when a new organization is created.
    """
    if created:
        try:
            service = SharedAPIKeyService()
            service.create_organization_keys(instance, instance.created_by)
        except Exception as e:
            # Log error but don't fail organization creation
            print(f"\n\nError creating API keys for organization {instance.name}: {e}\n\n")
