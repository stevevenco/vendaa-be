import abc
from .models import APIKey
from authentication.models import Organization


class ApiKeyService(abc.ABC):

    @abc.abstractmethod
    def create_api_key(self, organization, key_type, created_by=None, name=None, is_sandbox=False):
        pass

    @abc.abstractmethod
    def get_api_keys(self, organization):
        pass

    @abc.abstractmethod
    def revoke_api_key(self, organization, key_id):
        pass

    @abc.abstractmethod
    def create_organization_keys(self, organization, created_by=None, is_sandbox=False):
        pass

    @abc.abstractmethod
    def get_api_key_by_uuid(self, key_uuid, organization):
        pass


class ProductionApiKeyService(ApiKeyService):
    def get_api_key_by_uuid(self, key_uuid, organization):
        return APIKey.objects.get(uuid=key_uuid, organization=organization, is_sandbox=False)
    
    def create_api_key(self, organization, key_type, created_by=None, name=None, is_sandbox=False):
        if name not in ['Public Key', 'Secret Key']:
            raise ValueError("API key name must be either 'Public Key' or 'Secret Key'")
        APIKey.create_api_key(organization, key_type, created_by, name, is_sandbox)

    def create_organization_keys(self, organization, created_by=None, is_sandbox=False):
        APIKey.create_api_key(organization, 'public', created_by, 'Public Key', is_sandbox)
        APIKey.create_api_key(organization, 'secret', created_by, 'Secret Key', is_sandbox)

    def get_api_keys(self, organization):
        return APIKey.objects.filter(organization=organization, is_sandbox=False)

    def revoke_api_key(self, organization, key_id):
        # Logic to revoke a production API key
        raise NotImplementedError("Production API key revocation not implemented yet.")


class SandboxApiKeyService(ApiKeyService):
    def get_api_key_by_uuid(self, key_uuid, organization):
        return APIKey.objects.get(uuid=key_uuid, organization=organization, is_sandbox=True)

    def create_api_key(self, organization, key_type, created_by=None, name=None, is_sandbox=True):
        if name not in ['Public Key', 'Secret Key']:
            raise ValueError("API key name must be either 'Public Key' or 'Secret Key'")
        APIKey.create_api_key(organization, key_type, created_by, name, is_sandbox)

    def create_organization_keys(self, organization, created_by=None, is_sandbox=True):
        APIKey.create_api_key(organization, 'public', created_by, 'Public Key', is_sandbox)
        APIKey.create_api_key(organization, 'secret', created_by, 'Secret Key', is_sandbox)

    def get_api_keys(self, organization):
        return APIKey.objects.filter(organization=organization, is_sandbox=True)

    def revoke_api_key(self, organization, key_id):
        raise NotImplementedError("Production API key revocation not implemented yet.")


class SharedAPIKeyService(ApiKeyService):
    def create_api_key(self, organization, name, created_by=None):
        raise NotImplementedError("Shared API key service does not support this operation.")

    def get_api_keys(self, organization):
        raise NotImplementedError("Shared API key service does not support this operation.")

    def revoke_api_key(self, organization, key_id):
        raise NotImplementedError("Shared API key service does not support this operation.")

    def get_api_key_by_uuid(self, key_uuid, organization):
        raise NotImplementedError("Shared API key service does not support this operation.")

    def create_organization_keys(self, organization, created_by=None):
        # Create production keys
        try:
            print(f"\n\nCreating production API keys for organization {organization.name}")
            production_api_key_service = ProductionApiKeyService()
            production_api_key_service.create_organization_keys(organization, created_by, is_sandbox=False)
            print(f"\n\nSuccessfully created production API keys for organization {organization.name}\n")
        except Exception as e:
            raise Exception(f"Failed to create production API keys: {e}")

        # Create sandbox keys
        try:
            print(f"\n\nCreating sandbox API keys for organization {organization.name}")
            sandbox_api_key_service = SandboxApiKeyService()
            sandbox_api_key_service.create_organization_keys(organization, created_by, is_sandbox=True)
            print(f"\n\nSuccessfully created sandbox API keys for organization {organization.name}\n")
        except Exception as e:
            raise Exception(f"Failed to create sandbox API Keys: {e}")


def get_api_key_service(organization):
    if organization.is_sandbox:
        return SandboxApiKeyService()
    return ProductionApiKeyService()
