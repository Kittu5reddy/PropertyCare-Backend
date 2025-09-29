from fastapi import FastAPI, Response, Depends, HTTPException, Request, Cookie
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
from config import settings
import string
import random
from app.core.controllers.auth.email import SMTP_PORT,SMTP_SERVER,EMAIL_ADDRESS,EMAIL_PASSWORD
from app.core.models import redis_set_data,AsyncSession,get_db
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================
# CONFIG
# ======================
ACCESS_TOKEN_SECRET_KEY_ADMIN = settings.ACCESS_TOKEN_SECRET_KEY_ADMIN         
REFRESH_TOKEN_SECRET_KEY_ADMIN = settings.REFRESH_TOKEN_SECRET_KEY_ADMIN          
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN    
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN      
ADMIN_EMAILS=settings.ADMINS_EMAILS
OTP_EXPIRY_MINUTES=settings.OTP_EXPIRY_MINUTES
BLACK_LIST_TIME=settings.BLACK_LIST_TIME

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
    """Send login OTP email to admin with professional template"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"VPC ADMIN LOGIN <{EMAIL_ADDRESS}>"
        msg['To'] = email
        msg['Subject'] = "Your Vibhoos Propcare Verification Code"

        # Split OTP into individual digits for the template
        otp_digits = list(otp.ljust(6, '0')[:6])  # Ensure 6 digits, pad with 0 if needed
        
        # Get current year
        current_year = datetime.now().year
        
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="format-detection" content="telephone=no">
            <title>Email OTP Verification</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: Arial, Helvetica, sans-serif; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
            <!-- Email Container -->
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f3f4f6;">
                <tr>
                    <td align="center" style="padding: 20px 10px;">
                        <!-- Main Email Content -->
                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                            <!-- Email Header with Logo -->
                            <tr>
                                <td style="background-color: #f9fafb; padding: 30px 40px 20px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                                    <img src="https://uploadthingy.s3.us-west-1.amazonaws.com/uCmrv4YNGkminyPEBDKiSe/WhatsApp_Image_2025-09-26_at_19.07.02_626da1d9.jpg" 
                                         alt="Vibhoos Propcare Logo" 
                                         width="120" 
                                         height="auto" 
                                         style="display: block; margin: 0 auto; max-width: 120px; height: auto;">
                                </td>
                            </tr>
                            
                            <!-- Email Body -->
                            <tr>
                                <td style="padding: 40px; background-color: #f9fafb;">
                                    <!-- Greeting -->
                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                        <tr>
                                            <td style="color: #374151; font-size: 16px; line-height: 24px; margin-bottom: 20px;">
                                                Hello,{email}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="color: #374151; font-size: 16px; line-height: 24px; padding-bottom: 20px;">
                                                Thank you for using Vibhoos Propcare services. To complete your admin login verification, please use the following verification code:
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- OTP Code Section -->
                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                        <tr>
                                            <td style="background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 30px 20px; text-align: center; margin: 20px 0;">
                                                <!-- OTP Label -->
                                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                                    <tr>
                                                        <td style="color: #0f766e; font-size: 14px; line-height: 20px; text-align: center; padding-bottom: 15px;">
                                                            Your verification code is:
                                                        </td>
                                                    </tr>
                                                </table>
                                                
                                                <!-- OTP Digits Container -->
                                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                                    <tr>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[0]}</td>
                                                        <td style="width: 8px;"></td>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[1]}</td>
                                                        <td style="width: 8px;"></td>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[2]}</td>
                                                        <td style="width: 8px;"></td>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[3]}</td>
                                                        <td style="width: 8px;"></td>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[4]}</td>
                                                        <td style="width: 8px;"></td>
                                                        <td style="width: 50px; height: 50px; background-color: #ffffff; border: 2px solid #5eead4; border-radius: 8px; text-align: center; vertical-align: middle; font-size: 24px; font-weight: bold; color: #115e59; margin: 0 4px;">{otp_digits[5]}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Additional Instructions -->
                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                        <tr>
                                            <td style="color: #374151; font-size: 16px; line-height: 24px; padding: 20px 0 10px 0;">
                                                This code will expire in <strong>3 minutes</strong>. If you did not request this code, please ignore this email or contact our support team if you have concerns.
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="color: #374151; font-size: 16px; line-height: 24px; padding-bottom: 20px;">
                                                For security reasons, please do not share this code with anyone.
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="color: #374151; font-size: 16px; line-height: 24px;">
                                                Thank you,<br>
                                                <strong>The Vibhoos Propcare Team</strong>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Email Footer -->
                            <tr>
                                <td style="background-color: #ffffff; padding: 30px 40px; border-top: 1px solid #e5e7eb;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                        <tr>
                                            <td style="color: #6b7280; font-size: 12px; line-height: 18px; text-align: center; padding-bottom: 10px;">
                                                This is an automated message, please do not reply to this email.
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="color: #6b7280; font-size: 12px; line-height: 18px; text-align: center;">
                                                © {current_year} Vibhoos Propcare Private Limited. All rights reserved.<br>
                                                <em>Safeguarding Your Properties, Always.</em>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # GoDaddy SMTP (SSL port 465)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        print(f"✅ Professional OTP email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send OTP email: {str(e)}")
        return False




def get_current_admin_refresh_token(token: str):
    try:
        sub = verify_refresh_token(token)
        email = sub.get("email", None)
        admin_id = sub.get("admin_id", None)
        if email and email in EMAIL_ADDRESS and EMAIL_ADDRESS[email] == admin_id:
            return sub
        raise HTTPException(status_code=401, detail="Token tampered or invalid")
    except Exception as e:
        # Log exception if needed
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_current_admin_access_token(token:str,db:AsyncSession=Depends(get_db)):
    sub=verify_token(token)
    email=sub.get("email",None)
    admin_id=sub.get("admin_id",None)
    if email:
        if email in EMAIL_ADDRESS and EMAIL_ADDRESS[email]==admin_id:
            return sub

    raise HTTPException(status_code=401,detail="tampered")    