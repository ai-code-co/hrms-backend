from django.core import signing

# ------------------------------------------------------------------
# SIGNERS & CONSTANTS
# ------------------------------------------------------------------

# Separate signers for different purposes to prevent token cross-over
RESET_SIGNER = signing.TimestampSigner(salt='password-reset')
SETUP_SIGNER = signing.TimestampSigner(salt='password-setup')
EMAIL_SIGNER = signing.TimestampSigner(salt='email-verification')

RESET_TOKEN_EXPIRY = 24 * 60 * 60  # 24 hours
SETUP_TOKEN_EXPIRY = 1 * 60 * 60   # 1 hour
EMAIL_TOKEN_EXPIRY = 7 * 24 * 60 * 60  # 7 days

# ------------------------------------------------------------------
# PASSWORD RESET TOKEN (Forgot Password)
# ------------------------------------------------------------------

def generate_password_reset_token(user_id):
    """Generates a signed, time-limited token for password reset."""
    return RESET_SIGNER.sign(str(user_id))

def verify_password_reset_token(token):
    """Verifies password reset token and checks expiry."""
    try:
        user_id = RESET_SIGNER.unsign(token, max_age=RESET_TOKEN_EXPIRY)
        return int(user_id)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return None

# ------------------------------------------------------------------
# PASSWORD SETUP TOKEN (First-time password after verification)
# ------------------------------------------------------------------

def generate_password_setup_token(user_id):
    """Generates token allowing user to set password for first time."""
    return SETUP_SIGNER.sign(str(user_id))

def verify_password_setup_token(token):
    """Validates password setup token."""
    try:
        user_id = SETUP_SIGNER.unsign(token, max_age=SETUP_TOKEN_EXPIRY)
        return int(user_id)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return None

# ------------------------------------------------------------------
# EMAIL VERIFICATION TOKEN
# ------------------------------------------------------------------

def generate_email_token(user_id):
    """Generates email verification token."""
    return EMAIL_SIGNER.sign(str(user_id))

def verify_email_token(token):
    """Verifies email token and checks expiry."""
    try:
        user_id = EMAIL_SIGNER.unsign(token, max_age=EMAIL_TOKEN_EXPIRY)
        return int(user_id)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return None

