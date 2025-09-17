# permissions.py - Add these to your existing permissions.py

from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist
from authentication.models import Organization, Membership


class APIKeyPermission(permissions.BasePermission):
    """
    Base permission class for API key access control
    """
    required_scope = None
    
    def has_permission(self, request, view):
        # If not API key user, delegate to other permission classes
        if not hasattr(request.user, 'is_api_key_user'):
            return True  # Let other permissions handle this
            
        api_key = request.auth
        if not api_key:
            return False
            
        # Check scope if required
        if self.required_scope and not api_key.has_scope(self.required_scope):
            return False
            
        # Check organization context if present
        org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid')
        if org_uuid:
            try:
                organization = Organization.objects.get(uuid=org_uuid)
            except Organization.DoesNotExist:
                return False

            # Ensure API key belongs to the organization being accessed
            if api_key.organization != organization:
                return False

            # Ensure sandbox keys can only access sandbox organizations
            if api_key.sandbox != organization.is_sandbox:
                return False

        return True


class MetersReadPermission(APIKeyPermission):
    """Permission for meters read-only access"""
    required_scope = 'meters:read'


class MetersFullPermission(APIKeyPermission):
    """Permission for full meters access"""
    required_scope = 'meters:full'


class OrganizationsFullPermission(APIKeyPermission):
    """Permission for full organizations access"""
    required_scope = 'organizations:full'


class OrganizationsReadPermission(APIKeyPermission):
    """Permission for full organizations access"""
    required_scope = 'organizations:read'


class AuthReadPermission(APIKeyPermission):
    """Permission for auth read access"""
    required_scope = 'auth:read'


class InvitationsFullPermission(APIKeyPermission):
    """Permission for full invitations access"""
    required_scope = 'invitations:full'


class WalletFullPermission(APIKeyPermission):
    """Permission for full wallet access"""
    required_scope = 'wallet:full'


class APIKeysFullPermission(APIKeyPermission):
    """Permission for full API keys access"""
    required_scope = 'apikeys:full'


class TokenPurchasePermission(APIKeyPermission):
    """Permission for token purchase"""
    required_scope = 'token_purchase:create'


class IsOrganizationMemberOrAPIKey(permissions.BasePermission):
    """
    Enhanced version of IsOrganizationMember that also supports API key access
    """
    
    def has_permission(self, request, view):
        # Handle API key authentication
        if hasattr(request.user, 'is_api_key_user'):
            api_key = request.auth
            org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid') or view.kwargs.get('organization_id')

            if org_uuid and str(api_key.organization.uuid) == str(org_uuid):
                return True
            return False
        
        # Handle regular JWT authentication
        if not request.user or not request.user.is_authenticated:
            return False
            
        org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid') or view.kwargs.get('organization_id')
        if not org_uuid:
            return False
            
        try:
            membership = Membership.objects.get(
                user=request.user, 
                organization__uuid=org_uuid
            )
            return True
        except Membership.DoesNotExist:
            return False


class IsOrganizationOwnerOrAdminOrAPIKey(permissions.BasePermission):
    """
    Enhanced version of IsOrganizationOwnerOrAdmin that also supports API key access
    """
    
    def has_permission(self, request, view):
        # Handle API key authentication
        if hasattr(request.user, 'is_api_key_user'):
            api_key = request.auth
            org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid')
            
            if org_uuid and str(api_key.organization.uuid) == str(org_uuid):
                # API keys have admin-level access
                return True
            return False
        
        # Handle regular JWT authentication
        if not request.user or not request.user.is_authenticated:
            return False
            
        org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid')
        if not org_uuid:
            return False
            
        try:
            membership = Membership.objects.get(
                user=request.user, 
                organization__uuid=org_uuid
            )
            return membership.role in ["owner", "admin"]
        except Membership.DoesNotExist:
            return False


class ScopedPermission(permissions.BasePermission):
    """
    A flexible permission class that checks scopes for API keys and falls back to other permissions
    """
    
    def __init__(self, scope=None, fallback_permission=None):
        self.scope = scope
        self.fallback_permission = fallback_permission
    
    def has_permission(self, request, view):
        # Handle API key authentication
        if hasattr(request.user, 'is_api_key_user'):
            api_key = request.auth
            
            # Check scope if provided
            if self.scope and not api_key.has_scope(self.scope):
                return False
                
            # Check organization context
            org_uuid = view.kwargs.get('org_uuid') or view.kwargs.get('uuid')
            if org_uuid and str(api_key.organization.uuid) != str(org_uuid):
                return False
                
            return True
        
        # Handle regular authentication with fallback permission
        if self.fallback_permission:
            permission_instance = self.fallback_permission()
            return permission_instance.has_permission(request, view)
            
        return request.user and request.user.is_authenticated


def create_scoped_permission(scope, fallback_permission=None):
    """
    Factory function to create scoped permission classes
    """
    class DynamicScopedPermission(ScopedPermission):
        def __init__(self):
            super().__init__(scope=scope, fallback_permission=fallback_permission)
    
    return DynamicScopedPermission