from django.core import signing
from django.contrib.auth import get_user_model

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
# HELPERS
# ------------------------------------------------------------------

def _make_token_data(user):
    """Combine user ID and a short slice of password hash for state validation."""
    # We use a slice of the hash to keep the token size reasonable.
    # We use the END of the hash because the beginning matches for the same algorithm/iterations.
    return f"{user.id}:{user.password[-20:]}"

# ------------------------------------------------------------------
# PASSWORD RESET TOKEN (Forgot Password)
# ------------------------------------------------------------------

def generate_password_reset_token(user):
    """Generates a signed, time-limited token for password reset."""
    return RESET_SIGNER.sign(_make_token_data(user))

def verify_password_reset_token(token):
    """Verifies password reset token and checks expiry + usage state."""
    try:
        data = RESET_SIGNER.unsign(token, max_age=RESET_TOKEN_EXPIRY)
        user_id, pwd_slice = data.split(":")
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Verify password hash hasn't changed since token was issued
        if user.password[-20:] != pwd_slice:
            return None
            
        return int(user_id)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError, get_user_model().DoesNotExist):
        return None

# ------------------------------------------------------------------
# PASSWORD SETUP TOKEN (First-time password after verification)
# ------------------------------------------------------------------

def generate_password_setup_token(user):
    """Generates token allowing user to set password for first time."""
    return SETUP_SIGNER.sign(_make_token_data(user))

def verify_password_setup_token(token):
    """Validates password setup token and usage state."""
    try:
        data = SETUP_SIGNER.unsign(token, max_age=SETUP_TOKEN_EXPIRY)
        user_id, pwd_slice = data.split(":")
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        if user.password[-20:] != pwd_slice:
            return None

        return int(user_id)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError, get_user_model().DoesNotExist):
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

