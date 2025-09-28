from fastapi import FastAPI, Response, Depends, HTTPException, Request, Cookie
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
from config import settings
import string
import random
from app.core.controllers.auth.email import SMTP_PORT,SMTP_SERVER,EMAIL_ADDRESS,EMAIL_PASSWORD
from app.core.models import redis_set_data
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# admin/login->email-> 200,401,404(not found)
# admin/verfify-login-> otp==otp-->(access_token),refresh_token
# admin/block-admin-email-> 3mins

# ======================
# CONFIG
# ======================
ACCESS_TOKEN_SECRET_KEY_ADMIN = settings.ACCESS_TOKEN_SECRET_KEY_ADMIN          # change this!         # change this!
REFRESH_TOKEN_SECRET_KEY_ADMIN = settings.REFRESH_TOKEN_SECRET_KEY_ADMIN          # change this!         # change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN    # short life
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN       # longer life
ADMIN_EMAILS=settings.ADMINS_EMAILS
OTP_EXPIRY_MINUTES=settings.OTP_EXPIRY_MINUTES


# ======================
# UTILS
# ======================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Use correct secret key
    return jwt.encode(to_encode, ACCESS_TOKEN_SECRET_KEY_ADMIN, algorithm=ALGORITHM)


def create_refresh_token(email: str):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "email": email,
        "exp": expire,
        "type": "refresh"  # optional, to distinguish from access tokens
    }
    token = jwt.encode(payload, ACCESS_TOKEN_SECRET_KEY_ADMIN, algorithm=ALGORITHM)
    return token

from jose import JWTError, jwt
from fastapi import HTTPException

def verify_refresh_token(token: str):
    """
    Verify a JWT refresh token.
    Returns the email if valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
        
        # Check if token type is refresh
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Return the email from the payload
        return payload.get("email")
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
    
def generate_otp(email: str):
    # Mix of digits + uppercase letters (length 4)
    characters = string.digits + string.ascii_uppercase
    otp = ''.join(random.choices(characters, k=4))
    expires = OTP_EXPIRY_MINUTES*60
    return otp,expires



import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(email: str, otp: str):
    """Send login OTP email to admin"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Your Admin Login OTP"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Admin Login Verification</h2>

            <p>Your OTP for login is:</p>
            <p style="font-size: 22px; font-weight: bold; color: #4CAF50;">{otp}</p>

            <p>This OTP is valid for <strong>3 minutes</strong>.</p>

            <hr>
            <p>If you didn’t request this, please ignore this email.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # GoDaddy SMTP (SSL port 465)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        print(f"✅ OTP email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send OTP email: {str(e)}")
        return False
