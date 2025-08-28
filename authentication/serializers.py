from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from authentication.exceptions import InvalidOTP

from .models import Invitation, Membership, Organization, User, OTP
from .utils import verify_otp

# from utils.serializers import BaseSerializer


class UserModelSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "organizations",
        ]
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
            user=user,
            organization=organization,
            role="owner",
            invited_by=user  # Self-invited when creating organization
        )
        return organization


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name"]


class InvitationCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.ROLE_CHOICES, default="member")

    class Meta:
        model = Invitation
        fields = ["email", "role"]

    def validate_email(self, value):
        organization = self.context.get("organization")
        if organization and Membership.objects.filter(
            organization=organization, user__email=value
        ).exists():
            raise serializers.ValidationError(
                "A user with this email is already a member of this organization."
            )

        # if (
        #     organization
        #     and Invitation.objects.filter(
        #         organization=organization, email=value, status="pending"
        #     ).exists()
        # ):
        #     raise serializers.ValidationError(
        #         "An invitation has already been sent to this email address for this organization."
        #     )

        return value


class InvitationDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    organization_uuid = serializers.UUIDField(
        source="organization.uuid", read_only=True
    )
    role = serializers.CharField(source="get_role_display", read_only=True)
    sent_by_email = serializers.EmailField(source="sent_by.email", read_only=True)
    sent_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "token",
            "email",
            "role",
            "organization_name",
            "organization_uuid",
            "sent_by_email",
            "sent_by_name",
            "status",
            "created",
            "expires_at"
        ]

    def get_sent_by_name(self, obj):
        if obj.sent_by:
            return f"{obj.sent_by.first_name} {obj.sent_by.last_name}"
        return None


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate(self, attrs):
        token = attrs.get("token")
        try:
            invitation = Invitation.objects.get(token=token, status="pending")
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired invitation token.")

        if invitation.expires_at < timezone.now():
            invitation.status = "expired"
            invitation.save()
            raise serializers.ValidationError("Invitation has expired.")

        user = self.context["request"].user
        if invitation.email != user.email:
            raise serializers.ValidationError("This invitation is not for you.")

        attrs["invitation"] = invitation
        return attrs


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone_number"]


class MemberListSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["uuid", "user", "role", "joined_at", "invited_by"]
        read_only_fields = ["uuid", "joined_at"]


class MemberRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["role"]

    def validate_role(self, value):
        if value not in dict(Membership.ROLE_CHOICES):
            raise serializers.ValidationError("Invalid role choice.")
        return value


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


class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES)

    def validate_purpose(self, value):
        if value not in dict(OTP.PURPOSE_CHOICES):
            raise serializers.ValidationError("Invalid purpose choice.")
        return value


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES)

    @transaction.atomic
    def validate(self, attrs):
        email = attrs.get("email")
        code = attrs.get("otp_code")
        purpose = attrs.get("purpose")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        from authentication.utils import verify_otp

        new_password = self.context.get("new_password")

        if not verify_otp(user, code, purpose, new_password=new_password):
            raise serializers.ValidationError("Invalid OTP")

        attrs["user"] = user
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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user