from rest_framework import permissions

from authentication.models import Membership
from .permissions_map import ROLE_PERMISSIONS


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


class AllowOnlyRetrieve(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to non-safe methods
        # (POST, PUT, DELETE) for authenticated users
        if request.method in ["GET", "UPDATE"]:
            return bool(request.user and request.user.is_authenticated)

        # Allow access to safe methods
        # (GET, HEAD, OPTIONS) only for staff users
        return bool(request.user and request.user.is_staff)


# class OrganizationPermission(permissions.BasePermission):
#     def get_organization_uuid(self, request, view):
#         organization_uuid = view.kwargs.get("org_uuid") or view.kwargs.get("uuid")
#         if organization_uuid:
#             return organization_uuid
        
#         # If not in kwargs, try to get it from request data
#         return request.data.get("organization")

#     def has_permission(self, request, view):
#         organization_uuid = self.get_organization_uuid(request, view)
#         if not organization_uuid:
#             return False
        
#         try:
#             membership = Membership.objects.get(
#                 user=request.user, organization__uuid=organization_uuid
#             )
#             return self.has_role_permission(membership)
#         except Membership.DoesNotExist:
#             return False

#     def has_role_permission(self, membership):
#         raise NotImplementedError("Subclasses must implement has_role_permission")


# class CanManageOrganization(OrganizationPermission):
#     """
#     Permission to allow users to manage the organization.
#     """
#     def has_role_permission(self, membership):
#         return membership.role in ["owner", "admin"]


# class CanViewWallet(OrganizationPermission):
#     """
#     Permission to allow users to view a wallet.
#     """
#     def has_role_permission(self, membership):
#         return membership.role in ["owner", "admin", "finance_manager", "operations_manager", "support_agent", "auditor", "developer", "member"]


# class CanFundWallet(OrganizationPermission):
#     """
#     Permission to allow users to fund a wallet.
#     """
#     def has_role_permission(self, membership):
#         return membership.role in ["owner", "admin", "finance_manager"]


# class CanViewMeter(OrganizationPermission):
#     """
#     Permission to allow users to view meters.
#     """
#     def has_role_permission(self, membership):
#         return membership.role in ["owner", "admin", "finance_manager", "operations_manager", "support_agent", "auditor", "developer"]


# class CanManageMeter(OrganizationPermission):
#     """
#     Permission to allow users to manage meters.
#     """
#     def has_role_permission(self, membership):
#         return membership.role in ["owner", "admin", "operations_manager"]


# class CanVendToken(OrganizationPermission):
    """
    Permission to allow users to vend tokens.
    """
    def has_role_permission(self, membership):
        return membership.role in ["owner", "admin", "operations_manager"]



class OrganizationPermission(permissions.BasePermission):
    def get_org_uuid(self, request, view):
        return view.kwargs.get("org_uuid") or view.kwargs.get("organization_id") or request.data.get("organization")

    def get_membership(self, request, view):
        org_uuid = self.get_org_uuid(request, view)
        if not org_uuid:
            return None
        try:
            return Membership.objects.get(user=request.user, organization__uuid=org_uuid)
        except Membership.DoesNotExist:
            return None


class HasOrgPermission(OrganizationPermission):
    """
    Generic permission that checks if a user's role allows a given feature/action.
    Use as: HasOrgPermission("meter", "view")
    """

    def __init__(self, feature, action):
        self.feature = feature
        self.action = action

    def __call__(self, *args, **kwargs):
        """
        Make this object behave like a class so DRF can instantiate it.
        Each time DRF calls `permission()`, return a fresh instance
        with the same feature/action.
        """
        return HasOrgPermission(self.feature, self.action)

    def has_permission(self, request, view):
        membership = self.get_membership(request, view)
        if not membership:
            return False
        print(f"\n\nRequest URL: {request.path}")
        print(f"User role: {membership.role}")
        print(f"Is user permitted: {membership.role in ROLE_PERMISSIONS.get(self.feature, {}).get(self.action, [])}\n\n")
        return membership.role in ROLE_PERMISSIONS.get(self.feature, {}).get(self.action, [])
