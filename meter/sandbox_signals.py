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
from wallet.models import Wallet
from wallet.wallet_service import get_wallet_service
from .models import Meter, UtilityCost, UtilityVend
from .meter_service import get_meter_service


def _vend_sandbox_meter_token(organization, meter, month_ago):
    """
    A helper function to perform a sandbox vending operation for a given meter and month.
    """
    try:
        token_type = 'credit'
        utility_cost = UtilityCost.objects.get(name=token_type)
        wallet = Wallet.objects.get(reference=organization)

        amount_to_charge = Decimal(random.uniform(10, 100))

        with db_transaction.atomic():
            # Lock wallet for update
            locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

            # Create a utility vend record
            utility_vend = UtilityVend.objects.create(
                meter=meter,
                amount=amount_to_charge,
                utility_cost=utility_cost,
                vend_reference=f"VEND-{uuid.uuid4().hex}",
                initiated_by=None,  # No user in signal
                status='pending',
                organization=organization
            )

            # 1. Get the meter service
            meter_service = get_meter_service(organization)

            # 2. Generate the token
            validated_data = {'amount': amount_to_charge}
            token_response = meter_service.generate_token(token_type, validated_data, meter)

            # 3. Charge the wallet
            wallet_service = get_wallet_service(organization)
            transaction = wallet_service.debit_wallet(
                wallet=locked_wallet,
                amount=amount_to_charge,
                reference=f"VEND-{meter.meter_number}-{utility_vend.uuid}",
                idempotency_key=str(uuid.uuid4()) # Use a new uuid for idempotency
            )
            utility_vend.transaction = transaction
            utility_vend.save()

            # Process response and save token
            data_list = token_response.get('data', {}).get('data', [])
            token = data_list[0].get("tokenDec") if data_list else None
            utility_vend.token = token

            utility_vend.token_details = token_response
            utility_vend.status = 'successful'

            # Set the created_at to a past date
            vend_date = datetime.now() - relativedelta(months=month_ago)
            utility_vend.created_at = vend_date
            utility_vend.save()

    except (UtilityCost.DoesNotExist, Wallet.DoesNotExist) as e:
        # Log the error but don't stop the organization creation
        # In a real application, you'd use a proper logger
        pass
    except Exception as e:
        # Log the error but don't stop the organization creation
        # In a real application, you'd use a proper logger
        pass


@receiver(post_save, sender=Organization)
def generate_historical_sandbox_data(sender, instance, created, **kwargs):
    """
    Signal handler to generate historical utility vends for a new sandbox organization.
    """
    if created and instance.is_sandbox and os.environ.get('PYTEST_RUNNING') != 'true':
        try:
            meters = Meter.objects.filter(organization=instance)
            if not meters.exists():
                # This might happen if the demo meters are not created yet.
                # The other signal should have already run.
                # We can call it here to be safe.
                meter_service = get_meter_service(instance)
                meter_service.create_demo_meters(instance)
                meters = Meter.objects.filter(organization=instance)

            for i in range(5):
                for meter in meters:
                    # Vend for each of the last 5 months
                    _vend_sandbox_meter_token(instance, meter, i)

        except Exception as e:
            # Log the error but don't stop the organization creation
            # In a real application, you'd use a proper logger
            pass
