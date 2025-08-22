from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView


from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    DashboardSerializer,
    OldVerifyOTPSerializer,
    OTPVerifySerializer,
    UserModelSerializer,
)
from .utils import create_otp, send_otp


class UserCreateView(CreateAPIView):
    """Generic View for Listing and Creating User Profiles"""

    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user = User.objects.create_user(**validated_data)
        email_otp = create_otp(user, purpose="signup")
        # user.save()
        user_email = user.email
        send_otp(user_email, email_otp)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


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
class OldVerifyOTPView(GenericAPIView):
    """Generic View for verifying OTP and updating
    user verification status
    """

    serializer_class = OldVerifyOTPSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            instance=request.user,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyOTPView(GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.data.get("purpose") == "password_reset":
            new_password = request.data.get("new_password")
            if not new_password:
                return Response(
                    {"detail": "New password is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request.data["new_password"] = new_password
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        return Response(
            {"detail": "OTP verified successfully."}, status=status.HTTP_200_OK
        )


class RequestOTPView(GenericAPIView):
    """Generic View for requesting OTP for email verification"""

    serializer_class = OTPVerifySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        purpose = request.data.get("purpose", "signup")

        if purpose in ["password_reset"]:
            return Response(
                {"detail": "You cannot perform this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_code = create_otp(user, purpose=purpose)
        send_otp(user.email, otp_code)

        return Response(
            {"detail": "OTP sent to your email."}, status=status.HTTP_200_OK
        )


class ForgotPasswordView(GenericAPIView):
    """Generic View for handling forgot password requests"""

    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            otp_code = create_otp(user, purpose="password_reset")
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
