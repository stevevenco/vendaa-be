import random
from django.core.management.base import BaseCommand, CommandError
from authentication.models import Organization
from meter.models import Meter
from wallet.wallet_service import get_wallet_service

class Command(BaseCommand):
    help = 'Seeds a sandbox organization with a pre-funded wallet and demo meters.'

    def add_arguments(self, parser):
        parser.add_argument('org_uuid', type=str, help='The UUID of the sandbox organization to seed.')

    def handle(self, *args, **options):
        org_uuid = options['org_uuid']
        try:
            organization = Organization.objects.get(uuid=org_uuid)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with UUID "{org_uuid}" does not exist.')

        if not organization.is_sandbox:
            self.stdout.write(self.style.WARNING(f'Organization "{organization.name}" is not a sandbox organization. No data will be seeded.'))
            return

        self.stdout.write(f'Seeding data for sandbox organization "{organization.name}"...')

        # 1. Create a pre-funded wallet
        wallet_service = get_wallet_service(organization, None)
        wallet = wallet_service.create_wallet(organization)
        self.stdout.write(self.style.SUCCESS(f'Successfully created and funded wallet with ID {wallet.wallet_id}.'))

        # 2. Create demo meters
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
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully created 5 demo meters.'))

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded data for organization "{organization.name}".'))
