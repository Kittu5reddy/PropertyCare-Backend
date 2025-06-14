from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "kaushikpalvai2004@gmail.com"
EMAIL_PASSWORD = "qtca zitr naez ilip"



def create_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    """Send verification email to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Verify Your Email Address"

        verification_link = f"http://127.0.0.1:8000/auth/verify-email?token={token}"

        body = f"""
        <html>
        <body>
            <h2>Welcome! Please verify your email address</h2>
            <p>Thank you for signing up. Please click the link below to verify your email address:</p>
            <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_link}</p>
            <p>This link will expire in 60 minutes.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
