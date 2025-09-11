from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import SecretAPIKey, PublicAPIKey, User
import hashlib
import hmac

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Api-Key "):
            return None

        try:
            _, key = auth_header.split()
            key = key[3:]  # strip "sk-" or "pk-"
            prefix, key = key.split(".")
            if key.startswith("sk-"):
                return SecretAPIKeyAuthentication.authenticate(request, key=key, prefix=prefix)
            elif key.startswith("pk-"):
                return PublicAPIKeyAuthentication.authenticate(request, key=key, prefix=prefix)
            else:
                raise AuthenticationFailed("Invalid API Key.")
        except ValueError:
            raise AuthenticationFailed("Invalid API Key format.")

    def authenticate_header(self, request):
        return "Api-Key"

class SecretAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request, **kwargs):
        key = kwargs.get("key")
        prefix = kwargs.get("prefix")

        try:
            api_key = SecretAPIKey.objects.get(prefix=prefix)
        except SecretAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid Secret API Key.")

        if api_key.revoked:
            raise AuthenticationFailed("API Key has been revoked.")

        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        if not hmac.compare_digest(hashed_key, api_key.hashed_key):
            raise AuthenticationFailed("Invalid Secret API Key.")

        # if not api_key.organization.is_active:
        #     raise AuthenticationFailed("Organization is inactive.")

        user = api_key.created_by
        if not user or not user.is_active:
            raise AuthenticationFailed("User is inactive or does not exist.")

        print(f"\nAuthenticated via Secret API Key")
        return (user, api_key)

    def authenticate_header(self, request):
        return "Api-Key"


class PublicAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request, **kwargs):
        key = kwargs.get("key")
        prefix = kwargs.get("prefix")

        try:
            api_key = PublicAPIKey.objects.get(prefix=prefix)
        except PublicAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid Public API Key.")

        if api_key.revoked:
            raise AuthenticationFailed("API Key has been revoked.")

        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        if not hmac.compare_digest(hashed_key, api_key.hashed_key):
            raise AuthenticationFailed("Invalid Public API Key.")

        user = api_key.created_by
        if not user or not user.is_active:
            raise AuthenticationFailed("User is inactive or does not exist.")

        print(f"\nAuthenticated via Public API Key")
        return (user, api_key)

    def authenticate_header(self, request):
        return "Api-Key"