from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authentication.exceptions import InvalidOTP

from .models import Organization, OrganizationMember, User
from .schema import UserInput
from .utils import verify_otp

# from utils.serializers import BaseSerializer


class UserModelSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, allow_blank=True)
    last_name = serializers.CharField(required=True, allow_blank=True)
    organization = serializers.CharField(required=True, allow_blank=True)

    class Meta:
        model = User
        fields = ["organization", "email", "password", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}

    def create(self, validated_data: UserInput):
        organization_name = validated_data.pop("organization", None)
        user = User.objects.create_user(**validated_data)
        if organization_name:
            organization = Organization.objects.create(
                name=organization_name, created_by=user
            )
            user.organization = organization
            user.save()
            OrganizationMember.objects.create(
                user=user, organization=organization, role="admin"
            )
        return user

    def to_representation(self, instance):
        """Overriding to remove Password Field when returning Data"""
        ret = super().to_representation(instance)
        ret.pop("password", None)
        return ret


class DashboardSerializer(serializers.Serializer):
    user_fname = serializers.CharField()
    portfolio_views = serializers.IntegerField()
    followers = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    wallet_balance = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=True
    )

    def validate(self, attrs):
        # Custom validation logic can be added here if needed
        return attrs


class OldVerifyOTPSerializer(serializers.Serializer):
    email_otp = serializers.CharField(
        max_length=6, min_length=6, required=True
    )

    class Meta:
        model = User
        fields = ["email_otp"]

    def validate_email_otp(self, value):
        user = self.context["request"].user
        e_otp = user.email_otp
        print("email_otp: ", value)
        print("e_otp: ", e_otp)

        if not verify_otp(value, e_otp):
            raise InvalidOTP

        return e_otp

    @transaction.atomic
    def save(self):
        user = self.context["request"].user
        user.is_verified = True
        user.email_otp = None
        user.save()
        # self.validated_data["otp"].delete()
        return


class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=["signup", "password_reset"])

    @transaction.atomic
    def validate(self, attrs):
        user = self.context["request"].user
        code = attrs.get("otp_code")
        purpose = attrs.get("purpose")

        from authentication.utils import verify_otp

        new_password = self.context["request"].data.get("new_password")

        if not verify_otp(user, code, purpose, new_password=new_password):
            raise serializers.ValidationError("Invalid OTP")

        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        credentials = {
            "email": attrs.get("email"),
            "password": attrs.get("password"),
        }

        user = authenticate(**credentials)

        if user:
            if not user.is_active:
                raise exceptions.AuthenticationFailed("User is deactivated")

            data = {}
            refresh = self.get_token(user)

            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)

            return data
        else:
            raise exceptions.AuthenticationFailed(
                "No active account found with the given credentials"
            )
