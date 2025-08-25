from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authentication.exceptions import InvalidOTP

from .models import Membership, Organization, User
from .utils import verify_otp

# from utils.serializers import BaseSerializer


class UserModelSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "organizations"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}
    
    def get_organizations(self, obj):
        memberships = obj.memberships.all()
        return [
            {
                "uuid": membership.organization.uuid,
                "name": membership.organization.name,
                "role": membership.role,
            }
            for membership in memberships
        ]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        """Overriding to remove Password Field when returning Data"""
        ret = super().to_representation(instance)
        ret.pop("password", None)
        return ret


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["uuid", "name", "created_by", "created"]
        read_only_fields = ["uuid", "created_by", "created"]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        organization = Organization.objects.create(
            created_by=user, **validated_data
        )
        Membership.objects.create(
            user=user, organization=organization, role="owner"
        )
        return organization


class MemberSerializer(serializers.ModelSerializer):
    user = UserModelSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Membership
        fields = ["uuid", "user", "user_id", "role", "joined_at"]
        read_only_fields = ["uuid", "joined_at"]

    def create(self, validated_data):
        organization = self.context["organization"]
        user_id = validated_data.pop("user_id")
        try:
            user = User.objects.get(uuid=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Check if membership already exists
        if Membership.objects.filter(user=user, organization=organization).exists():
            raise serializers.ValidationError("User is already a member of this organization")

        membership = Membership.objects.create(
            user=user, organization=organization, **validated_data
        )
        return membership


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
