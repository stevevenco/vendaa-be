import uuid
import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    GenericAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication

from authentication.api_key.authentication import APIKeyAuthentication
from authentication.api_key.permissions import InvitationsFullPermission, IsOrganizationMemberOrAPIKey, IsOrganizationOwnerOrAdminOrAPIKey, MembershipFullPermission, OrganizationsFullPermission, OrganizationsReadPermission, create_scoped_permission

from .models import Membership, Organization, User, Invitation
from .serializers import (
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    ResetForgotPasswordSerializer,
    DashboardSerializer,
    MemberSerializer,
    MemberListSerializer,
    MemberRoleUpdateSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    InvitationCreateSerializer,
    InvitationDetailSerializer,
    AcceptInviteSerializer,
    OTPVerifySerializer,
    RequestOTPSerializer,
    UserModelSerializer,
)
from .utils import create_otp, send_invitation_email, send_otp

# from utils.permissions import CanManageOrganization, IsOrganizationOwnerOrAdmin
from utils.permissions import HasOrgPermission, IsOrganizationOwnerOrAdmin

class UserCreateView(CreateAPIView):
    """Generic View for Listing and Creating User Profiles"""

    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        email_otp = create_otp(user, purpose="signup")
        send_otp(user.email, email_otp, purpose="signup", user_first_name=user.first_name)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class OrganizationListCreateView(ListCreateAPIView):
    serializer_class = OrganizationSerializer
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]

    def get_permissions(self):
        """Dynamic permissions based on request method and authentication"""
        if self.request.method == 'GET':
            # Read-only access for both public and secret keys
            permission_classes = [
                IsAuthenticated,
                OrganizationsFullPermission,
            ]
        else:
            # Write access only for secret keys and JWT users
            permission_classes = [
                IsAuthenticated,
                OrganizationsFullPermission,
            ]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if hasattr(self.request.user, 'is_api_key_user'):
            # API key users can only access their own organization
            return Organization.objects.filter(uuid=self.request.user.organization.uuid)
        else:
            # JWT users see organizations they're members of
            return Organization.objects.filter(
                memberships__user=self.request.user
            ).distinct().order_by('-created')

    def get_serializer_context(self):
        return {"request": self.request}


class OrganizationUpdateView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationSerializer
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        OrganizationsFullPermission,
        HasOrgPermission('organization', 'write')
    ]
    lookup_field = 'uuid'
    lookup_url_kwarg = "org_uuid"

    def get_queryset(self):
        if hasattr(self.request.user, 'is_api_key_user'):
            return Organization.objects.filter(uuid=self.request.user.organization.uuid)
        else:
            return Organization.objects.filter(
                memberships__user=self.request.user
            ).distinct()


class OrganizationInviteView(CreateAPIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    serializer_class = InvitationCreateSerializer
    permission_classes = [
        IsAuthenticated,
        InvitationsFullPermission,
        HasOrgPermission('invitation', 'write')
    ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if 'org_uuid' in self.kwargs:
            context["organization"] = get_object_or_404(
                Organization, uuid=self.kwargs["org_uuid"]
            )
        return context

    def perform_create(self, serializer):
        organization = self.get_serializer_context()["organization"]
        invitation = serializer.save(organization=organization)
        send_invitation_email(invitation)


class VerifyInviteView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = serializers.Serializer

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        if not token:
            return Response(
                {"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # First try to convert the token string to UUID
            token_uuid = uuid.UUID(token)
            invitation = Invitation.objects.get(token=token_uuid, status="pending")
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid token format."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Invitation.DoesNotExist:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_404_NOT_FOUND
            )

        if invitation.expires_at < timezone.now():
            invitation.status = "expired"
            invitation.save()
            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListInvitationsView(GenericAPIView):
    """
    List invitations based on type:
    - 'received': Shows invitations sent to the current user's email
    - 'sent': Shows invitations sent by organizations where user is admin/owner
    """
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    serializer_class = InvitationDetailSerializer
    permission_classes = [
        IsAuthenticated,
        InvitationsFullPermission,
        HasOrgPermission('invitation', 'read')
    ]

    def get_queryset(self):
        invite_type = self.request.query_params.get('type', 'received')
        org_uuid = self.kwargs.get('org_uuid')
        user = self.request.user

        if invite_type == 'sent':
            # Get organizations where user is admin or owner
            admin_orgs = Organization.objects.filter(
                memberships__user=user,
                memberships__role__in=['admin', 'owner']
            )
            return Invitation.objects.filter(
                organization__uuid=org_uuid,
                status__in=['pending']  # Only show active invites
            ).order_by('-created')
        else:  # received
            return Invitation.objects.filter(
                email=user.email,
                status__in=['pending']  # Only show active invites
            ).order_by('-created')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelInviteView(GenericAPIView):
    """Cancel an invitation (only by organization admin/owner/operations_manager)"""
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        InvitationsFullPermission,
    ]
    serializer_class = serializers.Serializer

    def post(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, token=invitation_id)

        # Check if user has permission to cancel
        if not Membership.objects.filter(
            user=request.user,
            organization=invitation.organization,
            role__in=[
                'admin',
                'owner',
                'operations_manager'
                ]
        ).exists():
            return Response(
                {"detail": "You don't have permission to cancel this invitation."},
                status=status.HTTP_403_FORBIDDEN
            )

        if invitation.status != 'pending':
            return Response(
                {"detail": "Only pending invitations can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = 'cancelled'
        invitation.save()
        return Response({"detail": "Invitation cancelled successfully."}, status=status.HTTP_200_OK)


class DeclineInviteView(GenericAPIView):
    """Decline an invitation (only by invited user)"""
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    serializer_class = serializers.Serializer
    permission_classes = [
        IsAuthenticated,
        InvitationsFullPermission,
        # IsOrganizationOwnerOrAdminOrAPIKey
    ]

    def post(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, token=invitation_id)
        
        # Check if invitation is for current user
        if invitation.email != request.user.email:
            return Response(
                {"detail": "This invitation is not for you."},
                status=status.HTTP_403_FORBIDDEN
            )

        if invitation.status != 'pending':
            return Response(
                {"detail": "Only pending invitations can be declined."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = 'declined'
        invitation.save()
        return Response({"detail": "Invitation declined successfully."}, status=status.HTTP_200_OK)


class AcceptInviteView(GenericAPIView):
    serializer_class = AcceptInviteSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = serializer.validated_data["invitation"]

        Membership.objects.get_or_create(
            user=request.user,
            organization=invitation.organization,
            defaults={
                "role": invitation.role,
                "invited_by": invitation.sent_by
            },
        )

        invitation.status = "accepted"
        invitation.save()

        return Response(
            {"detail": "Invitation accepted successfully."}, status=status.HTTP_200_OK
        )


class MemberListCreateView(ListCreateAPIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        InvitationsFullPermission,
        HasOrgPermission('invitation', 'read')
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MemberListSerializer
        return InvitationCreateSerializer

    def get_queryset(self):
        organization = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return Membership.objects.filter(organization=organization).order_by('-created')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if getattr(self, "swagger_fake_view", False):
            return context
        context["organization"] = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = self.get_serializer_context()["organization"]

        invitation = serializer.save(
            organization=organization,
            sent_by=request.user
        )
        send_invitation_email(invitation)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MemberDetailView(RetrieveUpdateDestroyAPIView):
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    permission_classes = [
        IsAuthenticated,
        MembershipFullPermission,
        HasOrgPermission('membership', 'write')
    ]
    lookup_field = "uuid"

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MemberRoleUpdateSerializer
        return MemberListSerializer

    def get_queryset(self):
        organization = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return Membership.objects.filter(organization=organization)

    def _check_last_owner_or_admin(self, instance, new_role=None):
        """Check if this is the last owner/admin in the organization"""
        organization = instance.organization
        if new_role:
            # For role updates - check if this would remove the last owner/admin
            if instance.role in ['owner', 'admin'] and new_role == 'member':
                remaining_admins = Membership.objects.filter(
                    organization=organization,
                    role__in=['owner', 'admin']
                ).exclude(uuid=instance.uuid).count()
                if remaining_admins == 0:
                    return False
        else:
            # For deletion - check if this is the last owner/admin
            if instance.role in ['owner', 'admin']:
                remaining_admins = Membership.objects.filter(
                    organization=organization,
                    role__in=['owner', 'admin']
                ).exclude(uuid=instance.uuid).count()
                if remaining_admins == 0:
                    return False
        return True

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Only allow role updates
        if set(request.data.keys()) - {'role'}:
            return Response(
                {"detail": "Only role field can be updated"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_role = request.data.get('role')
        if not self._check_last_owner_or_admin(instance, new_role):
            return Response(
                {"detail": "Cannot change role. Organization must have at least one owner or admin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if not self._check_last_owner_or_admin(instance):
            return Response(
                {"detail": "Cannot remove the last owner or admin from the organization"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetailView(GenericAPIView):
    """Generic View for retrieving user details"""
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    serializer_class = UserModelSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserUpdateView(GenericAPIView):
    """Generic View for updating user details"""

    serializer_class = UserModelSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyOTPView(GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        context = {}
        if request.data.get("purpose") == "password_reset":
            new_password = request.data.get("new_password")
            if not new_password:
                return Response(
                    {"detail": "New password is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            context["new_password"] = new_password

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"detail": "OTP verified successfully."}, status=status.HTTP_200_OK
        )


class RequestOTPView(GenericAPIView):
    serializer_class = RequestOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        try:
            user = User.objects.get(email=email)
            otp_code = create_otp(user, purpose=purpose)
            send_otp(user.email, otp_code, purpose=purpose, user_first_name=user.first_name)
            return Response(
                {"detail": "OTP sent to your email."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ChangePasswordView(GenericAPIView):
    """Generic View for changing user password"""

    serializer_class = ChangePasswordSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "password updated successfully"},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ResetForgotPasswordView(GenericAPIView):
    """Generic View for handling forgot password requests"""

    serializer_class = ResetForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        serializer.save(email=email)
        return Response(
            {"detail": "Password updated successfully!"},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
