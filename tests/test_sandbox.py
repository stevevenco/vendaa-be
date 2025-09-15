import pytest
from django.core.management import call_command
from authentication.models import Organization, User
from authentication.api_key.models import APIKey
from meter.models import Meter
from wallet.models import Wallet

@pytest.mark.django_db
def test_create_sandbox_organization_creates_sandbox_key():
    user = User.objects.create_user(email='test_sandbox_org_key@example.com', password='password')
    org = Organization.objects.create(name='Test Sandbox Org For Key', created_by=user, is_sandbox=True)

    assert APIKey.objects.filter(organization=org, key_type='secret').exists()
    api_key = APIKey.objects.get(organization=org, key_type='secret')
    assert api_key.sandbox is True
    assert api_key.key_id.startswith('sk_sandbox_')

@pytest.mark.django_db
def test_create_live_organization_creates_live_key():
    user = User.objects.create_user(email='test_live_org_key@example.com', password='password')
    org = Organization.objects.create(name='Test Live Org For Key', created_by=user, is_sandbox=False)

    assert APIKey.objects.filter(organization=org, key_type='secret').exists()
    api_key = APIKey.objects.get(organization=org, key_type='secret')
    assert api_key.sandbox is False
    assert api_key.key_id.startswith('sk_live_')

@pytest.mark.django_db
def test_seed_sandbox_data_command():
    user = User.objects.create_user(email='test_seed@example.com', password='password')
    org = Organization.objects.create(name='Test Seed Sandbox Org', created_by=user, is_sandbox=True)

    call_command('seed_sandbox_data', str(org.uuid))

    assert Wallet.objects.filter(reference=org).exists()
    wallet = Wallet.objects.get(reference=org)
    assert wallet.available_balance == 100000.00

    assert Meter.objects.filter(organization=org).count() == 5

@pytest.mark.django_db
def test_seed_sandbox_data_for_live_org():
    user = User.objects.create_user(email='test_seed_live@example.com', password='password')
    org = Organization.objects.create(name='Test Seed Live Org', created_by=user, is_sandbox=False)

    call_command('seed_sandbox_data', str(org.uuid))

    assert not Wallet.objects.filter(reference=org).exists()
    assert not Meter.objects.filter(organization=org).exists()
