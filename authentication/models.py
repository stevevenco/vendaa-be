import uuid
from datetime import timedelta
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

# import argon2
from utils.models import TrackObjectStateMixin


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # Explicitly set staff and superuser status
        user.is_staff = extra_fields.get("is_staff", False)
        user.is_superuser = extra_fields.get("is_superuser", False)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TrackObjectStateMixin):
    first_name = models.CharField(
        max_length=50, blank=True, null=True, default=None
    )
    last_name = models.CharField(
        max_length=50, blank=True, null=True, default=None
    )
    phone_number = models.CharField(
        max_length=20, blank=True, null=True, default=None
    )
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    USER_ID_FIELD = "uuid"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Organization(TrackObjectStateMixin):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_organizations",
    )
    def __str__(self):
        return self.name


class Membership(TrackObjectStateMixin):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="invited_memberships"
    )

    @property
    def joined_at(self):
        return self.created

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"


class OTP(TrackObjectStateMixin):
    PURPOSE_CHOICES = [
        ("signup", "Signup Verification"),
        ("password_reset", "Password Reset"),
        ("email_change", "Email Change"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="otps"
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_used(self):
        self.used = True
        self.save()


class Invitation(TrackObjectStateMixin):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
        ("declined", "Declined"),
        ("cancelled", "Cancelled"),
    ]

    ROLE_CHOICES = Membership.ROLE_CHOICES

    email = models.EmailField()
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="sent_invitations"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation for {self.email} to {self.organization.name}"


