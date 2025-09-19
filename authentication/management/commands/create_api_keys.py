import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import Organization
from authentication.api_key.models import APIKey


class Command(BaseCommand):
    help = 'Create API keys for existing organizations that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-uuid',
            type=str,
            help='Create API keys for specific organization UUID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        if options['org_uuid']:
            organizations = Organization.objects.filter(uuid=options['org_uuid'])
        else:
            organizations = Organization.objects.all()

        created_count = 0
        
        for org in organizations:
            # Check if organization already has API keys
            existing_secret = APIKey.objects.filter(organization=org, key_type='secret').exists()
            existing_public = APIKey.objects.filter(organization=org, key_type='public').exists()
            
            if existing_secret and existing_public:
                self.stdout.write(f"Organization '{org.name}' already has API keys")
                continue
            
            if options['dry_run']:
                self.stdout.write(
                    f"Would create API keys for organization '{org.name}' (UUID: {org.uuid})"
                )
                continue
            
            try:
                with transaction.atomic():
                    if not existing_secret:
                        secret_key, secret_full = APIKey.create_api_key(
                            organization=org,
                            key_type='secret',
                            created_by=org.created_by,
                            name='Default Secret Key'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"Created secret key for '{org.name}': {secret_key}, secret_full: {secret_full}")
                        )
                    
                    if not existing_public:
                        public_key, public_full = APIKey.create_api_key(
                            organization=org,
                            key_type='public',
                            created_by=org.created_by,
                            name='Default Public Key'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"Created public key for '{org.name}': public_key: {public_key}, public_full: {public_full}")
                        )
                    
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to create API keys for '{org.name}': {e}")
                )
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully processed {created_count} organizations")
            )

