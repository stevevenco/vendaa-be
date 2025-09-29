import hashlib
import random
from datetime import timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

import config.settings as settings
from authentication.models import OTP


def generate_otp_code():
    return str(random.randint(100000, 999999))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def create_otp(user, purpose: str, expiry_minutes=5) -> str:
    raw_code = generate_otp_code()
    hashed = hash_otp(raw_code)

    OTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=hashed,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )
    return raw_code  # To be sent via email


def verify_otp(user, code: str, purpose: str, **kwargs) -> bool:
    hashed_code = hash_otp(code)
    try:
        otp_obj = OTP.objects.filter(
            user=user,
            purpose=purpose,
            used=False,
            expires_at__gt=timezone.now(),
        ).latest("created")

        if otp_obj.code_hash == hashed_code:
            otp_obj.mark_used()

            if otp_obj.purpose == "signup" and not user.is_verified:
                user.is_verified = True
                user.save()
                return True
            elif otp_obj.purpose == "password_reset":
                user.set_password(kwargs.get("new_password"))
                user.save()
                return True

        return False
    except OTP.DoesNotExist:
        return False


def send_otp(receiver, otp, purpose=OTP.PURPOSE_CHOICES[0][0], **kwargs):
    context = {
        "otp": otp,
        "user_first_name": kwargs.get("user_first_name", "")
    }

    if purpose == OTP.PURPOSE_CHOICES[1][0]:  # password_reset
        subject = "Password Reset Request"
        template_name = "forgot_password_template.html"
    elif purpose == OTP.PURPOSE_CHOICES[0][0]:  # signup
        subject = "Complete your registration"
        template_name = "signup_template.html"

    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    to = receiver
    send_mail(
        subject, plain_message, from_email, [to], html_message=html_message
    )


def send_invitation_email(invitation):
    subject = f"Invitation to join {invitation.organization.name}"
    context = {
        "organization_name": invitation.organization.name,
        "role": invitation.get_role_display(),
        "invite_link": f"{settings.FRONTEND_URL}/accept-invite/{invitation.token}/",
        "sender_name": f"{invitation.sent_by.first_name} {invitation.sent_by.last_name}" if invitation.sent_by else "Administrator",
        "sender_email": invitation.sent_by.email if invitation.sent_by else "no-reply@vedaa.co",
    }
    html_message = render_to_string("invitation_email.html", context)
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    to = invitation.email
    send_mail(
        subject, plain_message, from_email, [to], html_message=html_message
    )

