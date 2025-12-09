
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from jinja2 import Environment, FileSystemLoader
from config import settings
from background_task.celery_app import celery_app

@celery_app.task(
    name="background_task.tasks.email_tasks.send_email_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_email_task(*args, **kwargs):
    """
    Generic Celery task for sending emails.
    Supports both positional and keyword arguments.
    Example call:
        send_email_task.delay(
            "Welcome to Vibhoos PropCare Newsletter",
            "kaushik@example.com",
            "newsletter_email.html",
            {"unsubscribe_url": "..."},
            header="NEWS LETTER"
        )
    """
    try:
        # Unpack safely (args[0..3] and kwargs)
        subject = args[0] if len(args) > 0 else kwargs.get("subject")
        to_email = args[1] if len(args) > 1 else kwargs.get("to_email")
        template_name = args[2] if len(args) > 2 else kwargs.get("template_name")
        context = args[3] if len(args) > 3 else kwargs.get("context", {})
        header = kwargs.get("header", "Vibhoos PropCare")

        print(f"📨 Sending email to {to_email} with subject '{subject}'")

        success = send_email(subject, to_email, template_name, context, header)
        if success:
            print(f"✅ Email sent successfully to {to_email}")
        else:
            print(f"❌ Failed to send email to {to_email}")
        return success

    except Exception as e:
        print(f"🚨 Error in send_email_task: {e}")
        raise e

# SMTP setup (GoDaddy)
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
WEB_EMAIL = settings.WEB_EMAIL
PHONE_NUMBER = settings.PHONE_NUMBER


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# (go up 3 levels from: app/core/controllers/emails/utils.py → app/core/controllers → app/core → app)

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "app", "user", "controllers", "emails", "templates")
print(TEMPLATE_DIR)
print(f"📁 Loading email templates from: {TEMPLATE_DIR}")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
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
