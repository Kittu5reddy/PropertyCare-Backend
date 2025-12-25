import pyotp
import qrcode
from io import BytesIO
import base64

def generate_mfa_qr(admin_email: str):
    secret = pyotp.random_base32()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=admin_email,
        issuer_name="YourCompany Admin"
    )

    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "qr_code": qr_base64
    }


def verify_mfa_token(secret: str, otp: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)



import bcrypt

def verify_backup_code(input_code: str, stored_hashes: list) -> bool:
    for h in stored_hashes:
        if bcrypt.checkpw(input_code.encode(), h.encode()):
            stored_hashes.remove(h)  # 🔥 remove used code
            return True
    return False


import secrets
import bcrypt

def generate_backup_codes(count: int = 8):
    plain_codes = []
    hashed_codes = []

    for _ in range(count):
        code = secrets.token_hex(4).upper()  # 8-char code
        plain_codes.append(code)

        hashed = bcrypt.hashpw(code.encode(), bcrypt.gensalt())
        hashed_codes.append(hashed.decode())

    return plain_codes, hashed_codes
