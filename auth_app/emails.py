import os
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_email_token, generate_password_reset_token
from dotenv import load_dotenv

load_dotenv()


def send_password_reset_email(user):
    token = generate_password_reset_token(user.id)

    reset_url = f"{os.environ.get('BASE_URL_FRONTEND')}/reset-password?token={token}"
    # 👆 frontend URL (React/Vue/etc)

    subject = "Reset your HRMS password"

    message = f"""
Hi {user.first_name},

You requested to reset your password.

Click the link below to set a new password:
{reset_url}

This link expires in 24 hours.

If you did not request this, please ignore this email.

HRMS Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_verification_email(user):
    token = generate_email_token(user.id)
    verify_url = f"http://127.0.0.1:8000/auth/verify-email/{token}/"

    subject = "Verify your HRMS account"

    message = f"""
Hi {user.first_name},

Your account has been created.

Click the link below to verify your email:
{verify_url}

This link expires in 7 days.

HRMS Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
