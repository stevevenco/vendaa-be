from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import Organization
from .utils import create_wallet_for_organization

@receiver(post_save, sender=Organization)
def create_wallet_for_new_organization(sender, instance, created, **kwargs):
    """
    Signal handler to create a wallet when a new organization is created
    """
    if created:
        try:
            create_wallet_for_organization(instance)
        except Exception as e:
            # Log the error but don't stop the organization creation
            print(f"Error creating wallet for organization {instance.uuid}: {str(e)}")
