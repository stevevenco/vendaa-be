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


def send_otp(receiver, otp):
    subject = "OTP for Vendaa email verification"
    html_message = render_to_string("mail_template.html", {"otp": otp})
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    to = receiver
    send_mail(
        subject, plain_message, from_email, [to], html_message=html_message
    )
