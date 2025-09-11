from rest_framework import permissions

from authentication.models import Membership, SecretAPIKey, PublicAPIKey


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to only allow members of an organization to access a resource.
    """

    def has_permission(self, request, view):
        organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("organization_id")
        if not organization_uuid:
            return False
        try:
            if not request.user or not request.user.is_authenticated:
                return False
            return Membership.objects.filter(
                user=request.user, organization__uuid=organization_uuid
            ).exists()
        except (Membership.DoesNotExist, TypeError, ValueError):
            return False


class IsOrganizationOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners or admins of an organization to edit it.
    """

    def has_permission(self, request, view):
        organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("uuid") or view.kwargs.get("organization_id")
        if not organization_uuid:
            return False
        try:
            if not request.user or not request.user.is_authenticated:
                return False
            membership = Membership.objects.get(
                user=request.user, organization__uuid=organization_uuid
            )
            return membership.role in ["owner", "admin"]
        except (Membership.DoesNotExist, TypeError, ValueError):
            return False

# --- Internal API Scope Checking Helpers ---
class _HasAPIScope(permissions.BasePermission):
    """Internal helper to check scopes on a request assumed to be from an API key."""
    def has_permission(self, request, view):
        required_scopes = getattr(view, "required_scopes", [])
        if not required_scopes:
            return True
        key_scopes = request.auth.get_scopes()
        if "*" in key_scopes:
            return True
        return any(scope in key_scopes for scope in required_scopes)

class _HasPublicAPIScope(_HasAPIScope):
    """Internal helper for public key type and scope."""
    def has_permission(self, request, view):
        if not isinstance(request.auth, PublicAPIKey):
            return False
        return super().has_permission(request, view)

class _HasSecretAPIScope(_HasAPIScope):
    """Internal helper for secret key type and scope."""
    def has_permission(self, request, view):
        if not isinstance(request.auth, SecretAPIKey):
            return False
        return super().has_permission(request, view)


# --- New Composite/Primary Permission Classes ---

class IsOrganizationMemberOrHasScope(permissions.BasePermission):
    """
    Allows access if:
    - Request is from a regular user who is a member of the organization.
    - Request is from an API key (public or secret) that belongs to the organization and has the required scopes.
    """
    def has_permission(self, request, view):
        if request.auth and hasattr(request.auth, "prefix"):  # API Key request
            organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("organization_id")
            if not organization_uuid or str(request.auth.organization.uuid) != str(organization_uuid):
                return False

            required_key_type = getattr(view, "required_key_type", None)
            if required_key_type == 'public':
                return _HasPublicAPIScope().has_permission(request, view)
            if required_key_type == 'secret':
                return _HasSecretAPIScope().has_permission(request, view)
            # If no key type is specified, either is fine, just check scopes
            return _HasAPIScope().has_permission(request, view)

        # Not an API key request, check for standard user membership
        return IsOrganizationMember().has_permission(request, view)


class IsOrganizationOwnerOrAdminOrHasSecretScope(permissions.BasePermission):
    """
    Allows access if:
    - User is an authenticated organization owner/admin (via JWT/session).
    - Request uses a valid Secret API key with the required scope.
    """
    def has_permission(self, request, view):
        if request.auth and hasattr(request.auth, "prefix"):  # API Key request
            # This permission implies secret key access
            if not isinstance(request.auth, SecretAPIKey):
                return False

            organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("uuid") or view.kwargs.get("organization_id")
            if organization_uuid and str(request.auth.organization.uuid) != str(organization_uuid):
                return False # Key must match org if org is in URL

            return _HasSecretAPIScope().has_permission(request, view)

        # Not an API key request, check for owner/admin role
        return IsOrganizationOwnerOrAdmin().has_permission(request, view)


class IsSecretKeyWithScope(permissions.BasePermission):
    """
    Allows access only if the request uses a valid Secret API key with the required scope.
    Blocks regular user sessions.
    """
    def has_permission(self, request, view):
        if not (request.auth and hasattr(request.auth, "prefix")):
            return False  # Not an API key

        if not isinstance(request.auth, SecretAPIKey):
            return False # Must be a secret key

        organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("organization_id")
        if organization_uuid and str(request.auth.organization.uuid) != str(organization_uuid):
            return False

        return _HasSecretAPIScope().has_permission(request, view)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user


class IsWriteOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to non-safe methods
        # (POST, PUT, DELETE) for authenticated users
        if request.method not in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        # Allow access to safe methods
        # (GET, HEAD, OPTIONS) only for staff users
        return bool(request.user and request.user.is_staff)


class IsReadOnlyOrAdmin(permissions.BasePermission):
    """
    Permission to only allow read-only access to a resource.
    And Write access for admin users.
    """

    def has_permission(self, request, view):
        if request.method == "GET":
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class AllowOnlyRetrieve(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to non-safe methods
        # (POST, PUT, DELETE) for authenticated users
        if request.method in ["GET", "UPDATE"]:
            return bool(request.user and request.user.is_authenticated)

        # Allow access to safe methods
        # (GET, HEAD, OPTIONS) only for staff users
        return bool(request.user and request.user.is_staff)
