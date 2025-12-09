from config import settings
from background_task.tasks.email_tasks import send_email_task  # Celery task

# SMTP / Config (only values needed for context or templates)
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
WEB_EMAIL = settings.WEB_EMAIL
PHONE_NUMBER = settings.PHONE_NUMBER
API_BASE_URL = settings.API_BASE_URL


# ==========================================================
#  SEND CONSULTATION EMAIL  (Celery)
# ==========================================================
def send_consultation_email(
    name: str,
    email: str,
    preferred_date=None,
    preferred_time=None,
    subject=None,
    comment=None
):
    """Queue consultation confirmation email via Celery."""

    formatted_date = preferred_date.strftime("%d %b, %Y") if preferred_date else "your chosen date"
    formatted_time = preferred_time.strftime("%I:%M %p") if preferred_time else "your preferred time"

    email_normalized = email.lower().strip()

    context = {
        "name": name,
        "subject": subject or "General Consultation",
        "preferred_date": formatted_date,
        "preferred_time": formatted_time,
        "unsubscribe_url": f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{email_normalized}",
        "company_profile_url": "https://vibhoospropcare.com/company_profile.pdf",
        "sop_url": "https://vibhoospropcare.com/sop_document.pdf",
        "service_portfolio": "https://vibhoospropcare.com/services",
        "comment": comment or "-",
    }

    send_email_task.delay(
        "Your Consultation Request - Vibhoos PropCare",
        email,
        "/general/consultation_email.html",
        context,
        header="Consultation Request"
    )

    print(f"📩 Consultation email queued → {email}")


# ==========================================================
#  SEND NEWSLETTER EMAIL (Celery)
# ==========================================================
def send_newsletter_email(to_email: str, context: dict):
    """Queue newsletter welcome email via Celery."""
    send_email_task.delay(
        "Welcome to Vibhoos PropCare Newsletter",
        to_email,
        "/general/newsletter_email.html",
        context,
        header="NEWS LETTER"
    )
    print(f"📩 Newsletter email queued → {to_email}")


# ==========================================================
#  EMAIL VERIFICATION
# ==========================================================
def send_verification_email(email: str, token: str):
    """Queue email verification message."""
    context = {
        "verification_link": f"{API_BASE_URL}/auth/verify-email?token={token}"
    }

    send_email_task.delay(
        "Verify Your Vibhoos PropCare Account",
        email,
        "/auth/user_verification_email.html",
        context,
        header="Account Verification"
    )

    print(f"📩 Verification email queued → {email}")


# ==========================================================
#  FORGOT PASSWORD EMAIL
# ==========================================================
async def send_forgot_password_email(email: str, reset_link: str, context: dict = None):
    """Queue forgot-password email via Celery."""
    context = context or {"reset_link": reset_link}

    send_email_task.delay(
        "Reset Your Vibhoos PropCare Password",
        email,
        "/auth/reset_password_email.html",
        context,
        header="RESET-PASSWORD"
    )

    print(f"📩 Forgot password email queued → {email}")


# ==========================================================
#  UTILS
# ==========================================================
import secrets

def create_verification_token():
    """Generate a secure token for verification links."""
    return secrets.token_urlsafe(32)
