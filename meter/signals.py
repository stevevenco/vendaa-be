import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import Organization
from .meter_service import get_meter_service

# @receiver(post_save, sender=Organization)
# def load_demo_meters_for_sandbox_organization(sender, instance, created, **kwargs):
#     """
#     Signal handler to create a wallet when a new organization is created.
#     This signal is disabled during tests.
#     """
#     if created and os.environ.get('PYTEST_RUNNING') != 'true':
#         try:
#             meter_service = get_meter_service(instance)
#             meter_service.create_demo_meters(instance)
#         except Exception as e:
#             # Log the error but don't stop the organization creation
#             print(f"Error creating wallet for organization {instance.uuid}: {str(e)}")
