

from django.core import signing




PASSWORD_SIGNER = signing.TimestampSigner()
PASSWORD_TOKEN_EXPIRY = 60 * 60  # 1 hour
def generate_password_setup_token(user_id):
    return PASSWORD_SIGNER.sign(str(user_id))


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

SIGNER = signing.TimestampSigner()
TOKEN_EXPIRY_DAYS = 7
def generate_email_token(user_id):
    return SIGNER.sign(str(user_id))  # ensure string


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

