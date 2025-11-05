from background_task.tasks.email_tasks import send_email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets
from config import settings
from datetime import datetime

# GoDaddy SMTP settings
SMTP_SERVER = "smtpout.secureserver.net"
SMTP_PORT = 465  # SSL port
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
PATH = settings.EMAIL_TOKEN_VERIFICATION
API_BASE_URL=settings.API_BASE_URL

def create_verification_token():
    return secrets.token_urlsafe(32)


from background_task.tasks.email_tasks import send_email_task
from config import settings

API_BASE_URL = settings.API_BASE_URL

def send_verification_email(email: str, token: str):
    """Send verification email asynchronously using Celery."""
    context = {
        "verification_link": f"{API_BASE_URL}/auth/verify-email?token={token}"
    }

    subject = "Verify Your Vibhoos PropCare Account"

    # 🔥 Send via Celery (background)
    send_email_task.delay(
        subject,
        email,
        "user_verification_email.html",
        context,
        header="Account Verification"
    )

    print(f"✅ Verification email queued for {email}")


async def send_forgot_password_email(email: str, reset_link: str, context: dict = None):
    """Send forgot password email asynchronously using Celery."""
    subject = "Reset Your Vibhoos PropCare Password"

    if context is None:
        context = {"reset_link": reset_link}

    # 🔥 Send via Celery (background)
    send_email_task.delay(
        subject,
        email,
        "reset_password_email.html",
        context,
        header="RESET-PASSWORD"
    )

    print(f"✅ Password reset email queued for {email}")


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

        # GoDaddy requires SSL on port 465
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send admin login alert email: {e}")
        return False





