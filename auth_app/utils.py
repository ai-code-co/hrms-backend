"""
utils.py

This file contains all token-related utilities.
We intentionally use Django's TimestampSigner instead of JWT here
because these tokens are:
- short-lived
- single-purpose
- NOT used for authentication sessions

Tokens generated here are:
1. Email verification tokens
2. Password setup tokens (first login)
3. Password reset tokens (forgot password)
"""


from django.core import signing

# ------------------------------------------------------------------
# PASSWORD RESET TOKEN (Forgot Password)
# ------------------------------------------------------------------

# Used when a user clicks "Forgot Password"
# Short expiry to reduce security risk

SIGNER = signing.TimestampSigner()
TOKEN_EXPIRY_DAYS = 1  # 🔒 password reset = short expiry (24 hrs)


"""
    Generates a signed, time-limited token for password reset.

    Args:
        user_id (int): ID of the user

    Returns:
        str: Signed token containing user_id + timestamp
"""
def generate_password_reset_token(user_id):
    return SIGNER.sign(user_id)
"""
    Verifies password reset token and checks expiry.

    Args:
        token (str): Token received from email

    Returns:
        int | None: user_id if valid, else None
"""
def verify_password_reset_token(token):
    try:
        user_id = SIGNER.unsign(
            token,
            max_age=TOKEN_EXPIRY_DAYS * 24 * 60 * 60
        )
        return user_id
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None




# ------------------------------------------------------------------
# PASSWORD SETUP TOKEN (First-time password after verification)
# ------------------------------------------------------------------

# Used immediately after email verification
# Short expiry because link is auto-redirected
PASSWORD_SIGNER = signing.TimestampSigner()
PASSWORD_TOKEN_EXPIRY = 60 * 60  # 1 hour

"""
    Generates token allowing user to set password for first time.

    Args:
        user_id (int)

    Returns:
        str
    """

def generate_password_setup_token(user_id):
    return PASSWORD_SIGNER.sign(str(user_id))

"""
    Validates password setup token.

    Args:
        token (str)

    Returns:
        int | None
    """
def verify_password_setup_token(token):
    try:
        user_id = PASSWORD_SIGNER.unsign(
            token,
            max_age=PASSWORD_TOKEN_EXPIRY
        )
        return int(user_id)
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None
# email first time

# ------------------------------------------------------------------
# EMAIL VERIFICATION TOKEN
# ------------------------------------------------------------------

# Used when admin creates user

SIGNER = signing.TimestampSigner()
TOKEN_EXPIRY_DAYS = 7

"""
    Generates email verification token.

    Args:
        user_id (int)

    Returns:
        str
    """
def generate_email_token(user_id):
    return SIGNER.sign(str(user_id))  # ensure string
"""
    Verifies email token and checks expiry.

    Args:
        token (str)

    Returns:
        int | None
    """

def verify_email_token(token):
    try:
        user_id = SIGNER.unsign(
            token,
            max_age=TOKEN_EXPIRY_DAYS * 24 * 60 * 60
        )
        return int(user_id)  # 🔥 FIX IS HERE
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None

