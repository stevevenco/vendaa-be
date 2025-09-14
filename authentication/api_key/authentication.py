# authentication.py - Create this new file or add to existing authentication.py

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from .models import APIKey


class APIKeyUser:
    """
    A user-like object that represents API key authentication
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.organization = api_key.organization
        self.is_authenticated = True
        self.is_active = True
        self.is_api_key_user = True

    @property
    def id(self):
        return f"apikey_{self.api_key.uuid}"
    
    @property  
    def username(self):
        return f"api_key_{self.api_key.key_id}"
    
    @property
    def email(self):
        return None
        
    def is_anonymous(self):
        return False
        
    def get_username(self):
        return self.username
        
    def has_perm(self, perm, obj=None):
        return False
        
    def has_perms(self, perm_list, obj=None):
        return False
        
    def has_module_perms(self, module):
        return False
        
    def __str__(self):
        return f"APIKeyUser({self.api_key.key_id})"


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication class that works alongside JWT authentication
    """
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request using API key
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            keyword, token = auth_header.split()
        except ValueError:
            return None
            
        if keyword.lower() != self.keyword.lower():
            return None
            
        # Check if this looks like an API key (starts with sk- or pk-)
        if not (token.startswith('sk-') or token.startswith('pk-')):
            return None
            
        return self.authenticate_api_key(token)
    
    def authenticate_api_key(self, token):
        """
        Validate the API key and return user and auth tuple
        """
        api_key = APIKey.validate_key(token)
        
        if not api_key:
            raise AuthenticationFailed('Invalid API key')
            
        if not api_key.is_active:
            raise AuthenticationFailed('API key is disabled')
            
        # Create API key user
        api_key_user = APIKeyUser(api_key)
        
        return (api_key_user, api_key)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return f'{self.keyword} realm="API Key Authentication"'


class CombinedAuthentication:
    """
    A utility class to handle both JWT and API Key authentication
    You can use this in your settings.py for REST_FRAMEWORK authentication classes
    """
    
    @staticmethod
    def get_authentication_classes():
        from rest_framework_simplejwt.authentication import JWTAuthentication
        return [
            APIKeyAuthentication,
            JWTAuthentication,
        ]
