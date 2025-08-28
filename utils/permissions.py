from rest_framework import permissions

from authentication.models import Membership


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


class AllowOnlyRetrieve(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to non-safe methods
        # (POST, PUT, DELETE) for authenticated users
        if request.method in ["GET", "UPDATE"]:
            return bool(request.user and request.user.is_authenticated)

        # Allow access to safe methods
        # (GET, HEAD, OPTIONS) only for staff users
        return bool(request.user and request.user.is_staff)
