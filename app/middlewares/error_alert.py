import traceback
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


ADMIN_EMAIL = "kaushikipynb@gmail.com"
FROM_EMAIL = "info@vibhoospropcare.com"
SMTP_SERVER="smtpout.secureserver.net"
SMTP_PORT="465"
EMAIL_PASSWORD="Propcare2025@"


def send_error_email(subject: str, content: str):
    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(content, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, ADMIN_EMAIL, msg.as_string())

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import traceback

from background_task.tasks.email_tasks import send_email_task  # <-- IMPORTANT


class ErrorNotifierMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except Exception as e:
            url = str(request.url)
            method = request.method
            headers = dict(request.headers)

            try:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8") if body_bytes else ""
            except:
                body = "Unable to read request body"

            tb = traceback.format_exc()

            context = {
    "exception": str(e),
    "url": url,
    "method": method,
    "headers": headers,
    "body": body,
    "traceback": tb
}


            # 🚀 SEND EMAIL USING CELERY
            send_email_task.delay(
                "🔥 FASTAPI INTERNAL ERROR ALERT",
                ADMIN_EMAIL,     # change to your error receiver email
                "error_alert.html",         # HTML template you will create
                context,  # context for Jinja template
                header="Vibhoos PropCare - ERROR"
            )

            # Return standard 500 response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
