import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Membership,
    Organization,
    User,
    Invitation,
    SecretAPIKey,
    PublicAPIKey,
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    ResetForgotPasswordSerializer,
    MemberRoleUpdateSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    InvitationCreateSerializer,
    InvitationDetailSerializer,
    AcceptInviteSerializer,
    OTPVerifySerializer,
    RequestOTPSerializer,
    UserModelSerializer,
    SecretAPIKeySerializer,
    SecretAPIKeyCreateSerializer,
    PublicAPIKeySerializer,
    PublicAPIKeyCreateSerializer,
    APIKeyRevokeSerializer,
    MemberListSerializer,
)
from .backends import APIKeyAuthentication
from .utils import create_otp, send_invitation_email, send_otp

from utils.permissions import (
    IsOrganizationOwnerOrAdminOrHasSecretScope,
    IsSecretKeyWithScope,
)


class UserCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        email_otp = create_otp(user, purpose="signup")
        send_otp(
            user.email, email_otp, purpose="signup", user_first_name=user.first_name
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class OrganizationListCreateView(ListCreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}


class OrganizationUpdateView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationUpdateSerializer
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["orgs:write"]
    lookup_field = "uuid"
    queryset = Organization.objects.all()


class OrganizationInviteView(ListCreateAPIView):
    serializer_class = InvitationCreateSerializer
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["invitations:write"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "org_uuid" in self.kwargs:
            context["organization"] = get_object_or_404(
                Organization, uuid=self.kwargs["org_uuid"]
            )
        return context

    def perform_create(self, serializer):
        organization = self.get_serializer_context()["organization"]
        invitation = serializer.save(organization=organization, sent_by=self.request.user)
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
            token_uuid = uuid.UUID(token)
            invitation = Invitation.objects.get(token=token_uuid, status="pending")
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid token format."},
                status=status.HTTP_400_BAD_REQUEST,
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


class ListInvitationsView(ListAPIView):
    serializer_class = InvitationDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        invite_type = self.request.query_params.get("type", "received")
        user = self.request.user

        if invite_type == "sent":
            admin_orgs = Organization.objects.filter(
                memberships__user=user, memberships__role__in=["admin", "owner"]
            )
            return Invitation.objects.filter(
                organization__in=admin_orgs, status__in=["pending", "declined"]
            ).order_by("-created")
        else:
            return Invitation.objects.filter(
                email=user.email, status="pending"
            ).order_by("-created")


class CancelInviteView(GenericAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["invitations:write"]
    serializer_class = serializers.Serializer

    def post(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, token=invitation_id)

        if not Membership.objects.filter(
            user=request.user,
            organization=invitation.organization,
            role__in=["admin", "owner"],
        ).exists():
            return Response(
                {"detail": "You don't have permission to cancel this invitation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != "pending":
            return Response(
                {"detail": "Only pending invitations can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = "cancelled"
        invitation.save()
        return Response(
            {"detail": "Invitation cancelled successfully."}, status=status.HTTP_200_OK
        )


class DeclineInviteView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    def post(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, token=invitation_id)

        if invitation.email != request.user.email:
            return Response(
                {"detail": "This invitation is not for you."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != "pending":
            return Response(
                {"detail": "Only pending invitations can be declined."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = "declined"
        invitation.save()
        return Response(
            {"detail": "Invitation declined successfully."}, status=status.HTTP_200_OK
        )


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
            defaults={"role": invitation.role, "invited_by": invitation.sent_by},
        )
        invitation.status = "accepted"
        invitation.save()
        return Response(
            {"detail": "Invitation accepted successfully."}, status=status.HTTP_200_OK
        )


class MemberListCreateView(ListCreateAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MemberListSerializer
        return InvitationCreateSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.required_scopes = ["invitations:write"]
        else:
            self.required_scopes = ["orgs:read"]
        return super().get_permissions()

    def get_queryset(self):
        organization = get_object_or_404(Organization, uuid=self.kwargs["org_uuid"])
        return Membership.objects.filter(organization=organization)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = get_object_or_404(Organization, uuid=self.kwargs["org_uuid"])
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = self.get_serializer_context()["organization"]
        invitation = serializer.save(organization=organization, sent_by=request.user)
        send_invitation_email(invitation)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class MemberDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["orgs:write"]
    lookup_field = "uuid"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return MemberRoleUpdateSerializer
        return MemberListSerializer

    def get_queryset(self):
        organization = get_object_or_404(Organization, uuid=self.kwargs["org_uuid"])
        return Membership.objects.filter(organization=organization)

    def _check_last_owner_or_admin(self, instance, new_role=None):
        organization = instance.organization
        if new_role:
            if instance.role in ["owner", "admin"] and new_role == "member":
                if (
                    Membership.objects.filter(
                        organization=organization, role__in=["owner", "admin"]
                    )
                    .exclude(uuid=instance.uuid)
                    .count()
                    == 0
                ):
                    return False
        else:
            if instance.role in ["owner", "admin"]:
                if (
                    Membership.objects.filter(
                        organization=organization, role__in=["owner", "admin"]
                    )
                    .exclude(uuid=instance.uuid)
                    .count()
                    == 0
                ):
                    return False
        return True

    def update(self, request, *args, **kwargs):
        if set(request.data.keys()) - {"role"}:
            return Response(
                {"detail": "Only role field can be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_role = request.data.get("role")
        if not self._check_last_owner_or_admin(self.get_object(), new_role):
            return Response(
                {
                    "detail": "Cannot change role. Organization must have at least one owner or admin"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._check_last_owner_or_admin(self.get_object()):
            return Response(
                {
                    "detail": "Cannot remove the last owner or admin from the organization"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class UserDetailView(GenericAPIView):
    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserUpdateView(GenericAPIView):
    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticated]

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
            send_otp(
                user.email,
                otp_code,
                purpose=purpose,
                user_first_name=user.first_name,
            )
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
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "password updated successfully"},
            status=status.HTTP_200_OK,
        )


class TestAPIKeyView(APIView):
    permission_classes = [IsSecretKeyWithScope]
    authentication_classes = [APIKeyAuthentication]
    required_scopes = ["auth:me:read"]

    def get(self, request, *args, **kwargs):
        return Response(
            {"detail": "API Key authentication successful."}, status=status.HTTP_200_OK
        )


class SecretAPIKeyListCreateView(ListCreateAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SecretAPIKeyCreateSerializer
        return SecretAPIKeySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.required_scopes = ["api-keys:write"]
        else:
            self.required_scopes = ["api-keys:read"]
        return super().get_permissions()

    def get_queryset(self):
        return SecretAPIKey.objects.filter(organization__uuid=self.kwargs["org_uuid"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return context

    def perform_create(self, serializer):
        api_key = serializer.save()
        self.key = api_key.key
        self.key_instance = api_key

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data={})
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        headers = self.get_success_headers(create_serializer.data)
        read_serializer = SecretAPIKeySerializer(self.key_instance)
        data = {"key": self.key, **read_serializer.data}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class SecretAPIKeyDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["api-keys:write"]
    serializer_class = SecretAPIKeySerializer
    lookup_field = "uuid"
    lookup_url_kwarg = "api_key_uuid"

    def get_queryset(self):
        return SecretAPIKey.objects.filter(organization__uuid=self.kwargs["org_uuid"])

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return APIKeyRevokeSerializer
        return self.serializer_class

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance.revoked = serializer.validated_data.get("revoked", instance.revoked)
        instance.save()
        read_serializer = SecretAPIKeySerializer(instance)
        return Response(read_serializer.data)


class PublicAPIKeyListCreateView(ListCreateAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PublicAPIKeyCreateSerializer
        return PublicAPIKeySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            self.required_scopes = ["api-keys:write"]
        else:
            self.required_scopes = ["api-keys:read"]
        return super().get_permissions()

    def get_queryset(self):
        return PublicAPIKey.objects.filter(organization__uuid=self.kwargs["org_uuid"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return context

    def perform_create(self, serializer):
        api_key = serializer.save()
        self.key = api_key.key
        self.key_instance = api_key

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data={})
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        headers = self.get_success_headers(create_serializer.data)
        read_serializer = PublicAPIKeySerializer(self.key_instance)
        data = {"key": self.key, **read_serializer.data}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class PublicAPIKeyDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationOwnerOrAdminOrHasSecretScope]
    required_scopes = ["api-keys:write"]
    serializer_class = PublicAPIKeySerializer
    lookup_field = "uuid"
    lookup_url_kwarg = "api_key_uuid"

    def get_queryset(self):
        return PublicAPIKey.objects.filter(organization__uuid=self.kwargs["org_uuid"])

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return APIKeyRevokeSerializer
        return self.serializer_class

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance.revoked = serializer.validated_data.get("revoked", instance.revoked)
        instance.save()
        read_serializer = PublicAPIKeySerializer(instance)
        return Response(read_serializer.data)


class ResetForgotPasswordView(GenericAPIView):
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
