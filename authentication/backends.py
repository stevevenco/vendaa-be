from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey, User
import hashlib
import hmac


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Api-Key "):
            return None

        try:
            _, key = auth_header.split()
            if not key.startswith("sk-"):
                raise ValueError
            key = key[3:]  # strip "sk-"
            prefix, key = key.split(".")
        except ValueError:
            raise AuthenticationFailed("Invalid API Key format.")

        try:
            api_key = APIKey.objects.get(prefix=prefix)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API Key.")

        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        if not hmac.compare_digest(hashed_key, api_key.hashed_key):
            raise AuthenticationFailed("Invalid API Key.")

        # if not api_key.organization.is_active:
        #     raise AuthenticationFailed("Organization is inactive.")

        user = api_key.created_by
        if not user or not user.is_active:
            raise AuthenticationFailed("User is inactive or does not exist.")

        return (user, api_key)

    def authenticate_header(self, request):
        return "Api-Key"
