import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import Organization
from .wallet_service import SharedWalletService, get_wallet_service

@receiver(post_save, sender=Organization)
def create_wallet_for_new_organization(sender, instance, created, **kwargs):
    """
    Signal handler to create a wallet when a new organization is created.
    This signal is disabled during tests.
    """
    if created and os.environ.get('PYTEST_RUNNING') != 'true':
        try:
            # wallet_service = get_wallet_service(instance)
            wallet_service = SharedWalletService()
            wallet_service.create_shared_wallet(instance)
        except Exception as e:
            # Log the error but don't stop the organization creation
            print(f"Error creating wallets for organization {instance.uuid}: {str(e)}")
