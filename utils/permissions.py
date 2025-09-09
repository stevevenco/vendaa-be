from rest_framework import permissions

from authentication.models import Membership, APIKey


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to only allow members of an organization to access a resource.
    """

    def has_permission(self, request, view):
        organization_uuid = view.kwargs.get("org_uuid")
        if not organization_uuid:
            return False
        try:
            return Membership.objects.filter(
                user=request.user, organization__uuid=organization_uuid
            ).exists()
        except Membership.DoesNotExist:
            return False


class IsOrganizationOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners or admins of an organization to edit it.
    """

    def has_permission(self, request, view):
        if view.kwargs.get("org_uuid"):
            organization_uuid = view.kwargs.get("org_uuid")
        elif view.kwargs.get("uuid"):
            organization_uuid = view.kwargs.get("uuid")
        try:
            membership = Membership.objects.get(
                user=request.user, organization__uuid=organization_uuid
            )
            return membership.role in ["owner", "admin"]
        except Membership.DoesNotExist:
            return False


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


class IsOrganizationMemberOrAPIToken(permissions.BasePermission):
    """
    Permission to allow access if the user is a member of the organization
    or if the request is authenticated with a valid API token for the organization.
    """

    def has_permission(self, request, view):
        # Check if authentication was done via API Key by checking for a unique attribute.
        if request.auth and hasattr(request.auth, "prefix"):
            organization_uuid_str = view.kwargs.get("org_uuid")
            if not organization_uuid_str:
                return False
            # Compare the string representation of the UUIDs to avoid type errors.
            # print(f"\n\nComparing API Key Organization UUID: {request.auth.organization.uuid} with Path UUID: {organization_uuid_str}")
            # print(f"Result: {str(request.auth.organization.uuid) == str(organization_uuid_str)}\n\n")
            return str(request.auth.organization.uuid) == str(organization_uuid_str)

        # If not API Key auth, fall back to standard organization membership check for JWT/session.
        return IsOrganizationMember().has_permission(request, view)


class AllowOnlyRetrieve(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to non-safe methods
        # (POST, PUT, DELETE) for authenticated users
        if request.method in ["GET", "UPDATE"]:
            return bool(request.user and request.user.is_authenticated)

        # Allow access to safe methods
        # (GET, HEAD, OPTIONS) only for staff users
        return bool(request.user and request.user.is_staff)
