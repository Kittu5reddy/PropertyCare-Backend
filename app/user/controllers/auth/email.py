from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets
from dotenv import load_dotenv
from config import settings


# Email settingsuration
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
PATH=settings.EMAIL_TOKEN_VERIFICATION


def create_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    """Send verification email to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Verify Your Email Address"

        verification_link = f"{PATH}/auth/verify-email?token={token}"

        body = f"""
        <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Welcome to PropertyCare! Please verify your email address</h2>
        
        <p>Thank you for signing up. Please click the link below to verify your email address:</p>
        
        <p>
            <a href="{verification_link}" 
               style="background-color: #4CAF50; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
        </p>
        
        <p>Or copy and paste this link into your browser:</p>
        <p>{verification_link}</p>
        
        <p>This link will expire in 60 minutes.</p>
        
        <hr>
        
        <h3>About PropertyCare</h3>
        <p>
            <strong>PropertyCare</strong> is your trusted partner in seamless property management.
            Whether you’re an owner, tenant, or agent, our platform helps you track maintenance,
            handle tenant requests, and keep everything organized—all in one place.
        </p>
        
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


def send_admin_login_alert_email(email: str, ip_address: str = None, user_agent: str = None):
    """Send an alert email to admin when a login occurs."""
    from datetime import datetime
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Admin Login Notification"

        # Compose dynamic info
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_info = f"<p><b>IP Address:</b> {ip_address}</p>" if ip_address else ""
        ua_info = f"<p><b>Device/Browser:</b> {user_agent}</p>" if user_agent else ""

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Admin Login Alert</h2>
                <p>
                    Your admin account was just logged into on <b>{time_str}</b>.
                </p>
                {ip_info}
                {ua_info}
                <p>If this was you, no action is needed.</p>
                <p><span style="color:red"><b>If this was not you</b></span>, please reset your password immediately and review your account security.</p>
                <hr>
                <p>This is an automated alert for your security.</p>
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
        print(f"Failed to send admin login alert email: {e}")
        return False
