from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Membership, Organization, User
from .serializers import (
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    DashboardSerializer,
    MemberSerializer,
    OrganizationSerializer,
    OTPVerifySerializer,
    RequestOTPSerializer,
    UserModelSerializer,
)
from .utils import create_otp, send_otp
from utils.permissions import IsOrganizationOwnerOrAdmin


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
        send_otp(user.email, email_otp)
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


class MemberListCreateView(ListCreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwnerOrAdmin]

    def get_queryset(self):
        organization = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return Membership.objects.filter(organization=organization)

    def get_serializer_context(self):
        organization = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return {"organization": organization}


class MemberDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwnerOrAdmin]
    lookup_field = "uuid"

    def get_queryset(self):
        organization = get_object_or_404(
            Organization, uuid=self.kwargs["org_uuid"]
        )
        return Membership.objects.filter(organization=organization)


class UserDetailView(GenericAPIView):
    """Generic View for retrieving user details"""

    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserUpdateView(GenericAPIView):
    """Generic View for updating user details"""

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
            send_otp(user.email, otp_code)
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
    permission_classes = [IsAuthenticated]

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
