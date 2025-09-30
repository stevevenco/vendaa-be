from abc import ABC, abstractmethod
import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
import boto3
from django.conf import settings
from django.utils.html import strip_tags
import dotenv

from authentication.models import OTP

dotenv.load_dotenv()


class BaseEmailClient(ABC):
    """Abstract email client class."""

    @abstractmethod
    def send_email(self, subject, recipient, template_name, context):
        """Send an email with given subject, recipient, template, and context."""
        pass
    
    @abstractmethod
    def send_invitation_email(self, invitation):
        """Send an invitation email."""
        pass
    
    @abstractmethod
    def send_otp(self, receiver, otp, purpose=OTP.PURPOSE_CHOICES[0][0], **kwargs):
        """Send an OTP email."""
        pass

class DevEmailClient(BaseEmailClient):
    def send_email(self, subject, recipient, template_name, context):
        html_body = render_to_string(template_name, context)
        text_body = "This is a dev environment email.\n\n" + html_body

        html_message = render_to_string("invitation_email.html", context)
        plain_message = strip_tags(html_message)
        from_email = settings.EMAIL_HOST_USER
        to = recipient
        send_mail(
            subject, plain_message, from_email, [to], html_message=html_message
        )
        return {"status": "sent (dev)"}

    def send_invitation_email(self, invitation):
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

    def send_otp(self, receiver, otp, purpose=OTP.PURPOSE_CHOICES[0][0], **kwargs):
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
        elif purpose == OTP.PURPOSE_CHOICES[3][0]:  # account_verification
            subject = "Account Verification"
            template_name = "account_verification.html"

        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        from_email = settings.EMAIL_HOST_USER
        to = receiver
        send_mail(
            subject, plain_message, from_email, [to], html_message=html_message
        )

class AWSSESEmailClient(BaseEmailClient):
    def __init__(self):
        self.ses = boto3.client(
            "ses",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        )

    def send_email(self, subject, recipient, template_name, context):
        html_body = render_to_string(template_name, context)
        text_body = "Please view this email in HTML format."

        response = self.ses.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        return response

    def send_invitation_email(self, invitation):
        subject = f"Invitation to join {invitation.organization.name}"
        context = {
            "organization_name": invitation.organization.name,
            "role": invitation.get_role_display(),
            "invite_link": f"{settings.FRONTEND_URL}/accept-invite/{invitation.token}/",
            "sender_name": f"{invitation.sent_by.first_name} {invitation.sent_by.last_name}" if invitation.sent_by else "Administrator",
            "sender_email": invitation.sent_by.email if invitation.sent_by else "no-reply@vedaa.co",
        }
        html_body = render_to_string("invitation_email.html", context)
        text_body = "You have been invited to join an organization."
        to = invitation.email
        response = self.ses.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        return response

    def send_otp(self, receiver, otp, purpose=OTP.PURPOSE_CHOICES[0][0], **kwargs):
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
        elif purpose == OTP.PURPOSE_CHOICES[3][0]:  # account_verification
            subject = "Account Verification"
            template_name = "account_verification.html"

        html_body = render_to_string(template_name, context)
        text_body = "You requested an OTP."
        to = receiver
        response = self.ses.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        return response


def get_email_client():
    """Factory function to get the appropriate email client based on environment."""
    env = settings.ENVIRONMENT

    if env == "dev":
        print("\n\n========Using DevEmailClient for email operations.========\n")
        return DevEmailClient()
    else:  # production
        print("\n\n========Using AWSSESEmailClient for email operations.========\n")
        return AWSSESEmailClient()