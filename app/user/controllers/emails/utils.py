from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from jinja2 import Environment, FileSystemLoader
from config import settings

# SMTP setup (GoDaddy)
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
WEB_EMAIL = settings.WEB_EMAIL
PHONE_NUMBER = settings.PHONE_NUMBER

# Jinja2 environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)
templates_dir = os.path.join(BASE_DIR, "templates")
env = Environment(loader=FileSystemLoader(templates_dir))

def send_email(subject: str, to_email: str, template_name: str, context: dict=None,header:str="Vibhoos PropCare"):
    """Generic function to send an email using a Jinja2 HTML template."""
    try:
        # Render HTML template
        template = env.get_template(template_name)
        html_content = template.render(**context)

        msg = MIMEMultipart()
        msg["From"] = f"{header} <{EMAIL_ADDRESS}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def send_consultation_email(
    name: str,
    email: str,
    preferred_date=None,
    preferred_time=None,
    subject=None,
    comment=None
):
    """Send a consultation confirmation email to the user."""

    # Normalize subject and handle date/time formatting safely
    formatted_date = preferred_date.strftime("%d %b, %Y") if preferred_date else "your chosen date"
    formatted_time = preferred_time.strftime("%I:%M %p") if preferred_time else "your preferred time"

    # Normalize email and prepare context for the email template
    email_normalized = email.lower().strip()

    context = {
        "name": name,
        "subject": subject or "General Consultation",
        "preferred_date": formatted_date,
        "preferred_time": formatted_time,
        "unsubscribe_url": f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{email_normalized}",
        "company_profile_url": "https://vibhoospropcare.com/company_profile.pdf",
        "sop_url": "https://vibhoospropcare.com/sop_document.pdf",  # (optional: replace with actual SOP URL)
        "service_portfolio": "https://vibhoospropcare.com/services",  # (optional)
        "comment":comment or "-"
    }

    # Send the email using your reusable send_email() function
    return send_email(
        subject="Your Consultation Request - Vibhoos PropCare",
        to_email=email,
        template_name="consultation_email.html",
        context=context,
        header="Consultation Request"
    )


def send_newsletter_email(to_email: str, context: dict):
    """Send a newsletter welcome email."""
    context = context
    return send_email("Welcome to Vibhoos PropCare Newsletter", to_email, "newsletter_email.html", context,header="NEWS LETTER")
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

