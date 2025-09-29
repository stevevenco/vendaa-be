import os
import uuid
import random
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db import transaction as db_transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import serializers

from authentication.models import Organization
from sandbox_feature_flag import POPULATE_SANDBOX_DEMO_METERS, POPULATE_SANDBOX_DEMO_VENDS
from wallet.models import Wallet
from wallet.wallet_service import get_wallet_service
from .models import Meter, UtilityCost, UtilityVend
from .meter_service import get_meter_service
from .utils import format_token


@receiver(post_save, sender=Organization)
def generate_historical_sandbox_data(sender, instance, created, **kwargs):
    """
    Signal handler to generate historical utility vends for a new sandbox organization.
    """
    print(f"\n\n=====Post-save signal triggered for Organization {instance.uuid}, created={created}, is_sandbox={instance.is_sandbox}====\n\n")
    if created and instance.is_sandbox and os.environ.get('PYTEST_RUNNING') != 'true':
        try:
            meters = Meter.objects.filter(organization=instance, is_sandbox=True)
            if not meters.exists():
                # This might happen if the demo meters are not created yet.
                # The other signal should have already run.
                # We can call it here to be safe.
                if POPULATE_SANDBOX_DEMO_METERS:
                    create_demo_meters(instance)
                meters = Meter.objects.filter(organization=instance, is_sandbox=True)

            if POPULATE_SANDBOX_DEMO_VENDS:
                for i in range(5):
                    for meter in meters:
                        # Vend for each of the last 5 months
                        _vend_sandbox_meter_token(instance, meter, i)

        except Exception as e:
            # Log the error but don't stop the organization creation
            print(f"Error generating historical sandbox data for organization {instance.uuid}: {str(e)}")


def create_demo_meters(organization: Organization):
        print(f"\n\nCreating demo meters for sandbox organization {organization.uuid}")
        for i in range(5):
            meter_number = f'SANDBOX-{random.randint(1000000000, 9999999999)}'
            Meter.objects.get_or_create(
                meter_number=meter_number,
                organization=organization,
                defaults={
                    'customer_name': f'Sandbox Customer {i + 1}',
                    'address': f'123 Sandbox Street, Demo City',
                    'meter_type': 'electricity',
                    'sgc': '12345',
                    'tariff_index': '1',
                    'key_revision_number': '1',
                    'is_sandbox': True,
                }
            )
            print(f"Created demo meter {meter_number} for organization {organization.uuid}")

def _vend_sandbox_meter_token(organization: Organization, meter: Meter, month_ago):
    """
    A helper function to perform a sandbox vending operation for a given meter and month.
    """
    print(f"\n\nVending for meter {meter.meter_number} for month offset {month_ago}\n\n")
    try:
        token_type = random.choice(["credit", "mse", "mgtk"])
        utility_cost = UtilityCost.objects.get(name=token_type)
        wallet = Wallet.objects.get(reference=organization, is_sandbox=True)
        token_class = random.choice(["Detect Tamper", "Disconnect On Tamper"])
        token_sub_class = {
            "Detect Tamper": random.choice(["Enable", "Disable"]),
            "Disconnect On Tamper": random.choice(["Enable", "Disable"])
        }

        amount_to_charge = Decimal(random.uniform(10, 100))

        with db_transaction.atomic():
            # Lock wallet for update
            locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

            # month to record tokrn vend
            vend_date = datetime.now() - relativedelta(months=month_ago)

            # Create a utility vend record
            utility_vend = UtilityVend.objects.create(
                meter=meter,
                amount=amount_to_charge,
                utility_cost=utility_cost,
                vend_reference=f"VEND-{uuid.uuid4().hex}",
                initiated_by=organization.created_by,  # No user in signal
                status='pending',
                organization=organization,
                is_sandbox=True,
                meter_number=meter.meter_number,
                meter_type=meter.meter_type,
                token_type=token_type,
                token_class=token_class if token_type == "mgtk" else None,
                token_sub_class=token_sub_class[token_class] if token_type == "mgtk" else None
            )

            # 1. Get the meter service
            meter_service = get_meter_service(organization, organization.created_by)

            # 2. Generate the token
            validated_data = {'amount': amount_to_charge}
            token_response = meter_service.generate_token(token_type, validated_data, meter)

            # 3. Charge the wallet
            wallet_service = get_wallet_service(organization, organization.created_by)
            transaction = wallet_service.debit_wallet(
                wallet=locked_wallet,
                amount=amount_to_charge,
                reference=f"VEND-{meter.meter_number}-{utility_vend.uuid}",
                idempotency_key=str(uuid.uuid4()) # Use a new uuid for idempotency
            )
            transaction.created = vend_date
            transaction.save()
            utility_vend.transaction = transaction
            utility_vend.save()

            # Process response and save token
            tokens = [item.get("tokenDec") for item in token_response.get('data', {}).get('data', [])]
            utility_vend.token = [format_token(token) for token in tokens]

            utility_vend.token_details = token_response
            utility_vend.status = 'Success'
            utility_vend.token_type = token_type
            utility_vend.meter_type = meter.meter_type
            utility_vend.meter_number = meter.meter_number

            # Set the created_at to a past date
            # vend_date = datetime.now() - relativedelta(months=month_ago)
            utility_vend.created = vend_date
            utility_vend.save()

    except (UtilityCost.DoesNotExist, Wallet.DoesNotExist) as e:
        print(f"Configuration or entity not found for sandbox vending: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during sandbox vending: {str(e)}")
