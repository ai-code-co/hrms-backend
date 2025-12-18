from django.core import signing

SIGNER = signing.TimestampSigner()
TOKEN_EXPIRY_DAYS = 7

def generate_email_token(user_id):
    return SIGNER.sign(user_id)

def verify_email_token(token):
    try:
        user_id = SIGNER.unsign(
            token,
            max_age=TOKEN_EXPIRY_DAYS * 24 * 60 * 60  # 7 days
        )
        return user_id
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None
