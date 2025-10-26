from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Depends
from app.core.validators.emails import NewsLetter as NewsLetterSchema
from app.core.models.newsletter import NewsLetter 
from app.core.models.consultation import Consultation  
from app.core.validators.consultation import Consultation as ConsultationSchema
from .utils import send_consultation_email,send_newsletter_email
email=APIRouter(prefix="/email",tags=['emails'])
from sqlalchemy import select
from app.core.models import get_db,AsyncSession
from .utils import *
from email.message import EmailMessage

from fastapi import BackgroundTasks
from email_validator import validate_email, EmailNotValidError
import dns.resolver



def send_newsletter(recipient_email, html_body):
    msg = EmailMessage()
    msg['Subject'] = 'Vibhoos PropCare Newsletter'
    msg['From'] = 'news@vibhoospropcare.com'
    msg['To'] = recipient_email
    # List-Unsubscribe headers for Gmail manage subscription
    msg['List-Unsubscribe'] = f'<https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{recipient_email}>'
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    msg.set_content(html_body, subtype='html')

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login('your_username', 'your_password')
        server.send_message(msg)

@email.post('/subscribe-news-letters')
async def news_letter_subscribe(
    payload: NewsLetterSchema, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Validate email format and domain
    try:
        v = validate_email(payload.email)
        email_normalized = v.email
        domain = email_normalized.split("@")[1]
        try:
            dns.resolver.resolve(domain, 'MX')
        except Exception:
            return {"error": "Email domain does not accept mail"}
    except EmailNotValidError as e:
        return {"error": str(e)}
    # Check if email exists
    data = await db.execute(select(NewsLetter).where(NewsLetter.email == email_normalized).limit(1))
    record = data.scalar_one_or_none()

    if not record:
        # Create new subscription
        record = NewsLetter(email=email_normalized, status=True)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        message = "subscribed successfully"
    else:
        if not record.status:
            # Reactivate subscription
            record.status = True
            db.add(record)
            await db.commit()
            await db.refresh(record)
            message = "subscribed successfully"
        else:
            return {"message": "already subscribed", "status": "active"}

    # Send newsletter email in background
    unsubscribe_url = f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{email_normalized}"
    background_tasks.add_task(send_newsletter_email, email_normalized, unsubscribe_url)

    return {"message": message, "status": "active"}


@email.get('/unsubscribe-news-letters/{email}', response_class=HTMLResponse)
async def unsubscribe_news_letter(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NewsLetter).where(NewsLetter.email == email).limit(1)
    )
    record = result.scalar_one_or_none()

    if record:
        record.status = False
        db.add(record)
        await db.commit()
        await db.refresh(record)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <title>Successfully Unsubscribed</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background-color: #f9fafb;">
        <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;">
        <h2 style="color: #16a34a; margin-bottom: 20px;">✓ Successfully Unsubscribed</h2>
        <p style="font-size: 18px; color: #374151; margin-bottom: 15px;">You have been successfully unsubscribed from the Vibhoos PropCare newsletter.</p>
        <p style="color: #6b7280; margin-bottom: 20px;">Email: <strong>{email}</strong></p>
        <p style="color: #6b7280; line-height: 1.5;">We're sorry to see you go. You can resubscribe anytime by visiting our website.</p>
        <div style="margin-top: 30px;">
        <a href="/" style="background-color: #0C4A6E; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 500;">
            Back to Home
        </a>
        </div>
        </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)

    html_not_found = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Email Not Found</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
    <h2>Email not found</h2>
    <p>The email <strong>{email}</strong> was not found in our subscription list.</p>
    <a href="https://www.vibhoospropcare.com" style="color: #0C4A6E; text-decoration: none;">Back to Home</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_not_found, status_code=404)


from fastapi import BackgroundTasks

@email.post('/book-consulting')
async def booking_consulting(
    payload: ConsultationSchema, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Validate email format and domain
    try:
        v = validate_email(payload.email)
        email_normalized = v.email
        domain = email_normalized.split("@")[1]
        try:
            dns.resolver.resolve(domain, 'MX')
        except Exception:
            return {"error": "Email domain does not accept mail"}
    except EmailNotValidError as e:
        return {"error": str(e)}

    record = Consultation(
        name=payload.name,
        email=email_normalized,
        phone=payload.phone,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        subject=payload.subject,
        comment=payload.comment
        
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)

    background_tasks.add_task(
        send_consultation_email,
        name=payload.name,
        email=email_normalized,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        subject=payload.subject
    )

    return {"message": "consultation booked successfully", "id": record.id}