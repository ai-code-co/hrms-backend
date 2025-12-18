from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_email_token

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
