












































from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Depends
from app.core.validators.emails import NewsLetter as NewsLetterSchema
from app.core.models.newsletter import NewsLetter 
from app.core.models.consultation import Consultation  
from app.core.validators.consultation import Consultation as ConsultationSchema

email=APIRouter(prefix="/email",tags=['emails'])
from sqlalchemy import select
from app.core.services.db import get_db
from sqlalchemy.ext.asyncio import (
    AsyncSession
)
from .utils import *


from fastapi import BackgroundTasks
from email_validator import validate_email, EmailNotValidError
import dns.resolver

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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
    context={
    "unsubscribe_url" : f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{email_normalized}",
    "company_profile_url" : f"https://vibhoospropcare.com/vibhoos_propcare_company_profile.pdf",
    "sop":f"https://vibhoospropcare.com/vibhoos_propcare_standard_operating_procedures.pdf",
    "service_portfolio":f"https://www.vibhoospropcare.com/services",
    "email":WEB_EMAIL,
    "website_url":"www.vibhoospropcare.com",
    "phone_number":PHONE_NUMBER,
    }
 
    send_email_task.delay("Welcome to Vibhoos PropCare Newsletter", email_normalized, "/general/newsletter_email.html", context,header="NEWS LETTER")


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


@email.post("/book-consulting")
async def booking_consulting(
    payload: ConsultationSchema, 
    db: AsyncSession = Depends(get_db)
):
    # ✅ 1. Validate email format and MX record
    try:
        v = validate_email(payload.email)
        email_normalized = v.email.lower().strip()
        domain = email_normalized.split("@")[1]
        dns.resolver.resolve(domain, "MX")
    except EmailNotValidError as e:
        return {"error": f"Invalid email: {str(e)}"}
    except Exception:
        return {"error": "Email domain does not accept mail"}

    # ✅ 2. Save booking details to DB
    record = Consultation(
        name=payload.name,
        email=email_normalized,
        phone=payload.phone,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        subject=payload.subject,
        comment=payload.comment or "-",
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)

    # ✅ 3. Prepare email context
    formatted_date = (
        payload.preferred_date.strftime("%d %b, %Y") 
        if payload.preferred_date else "your chosen date"
    )
    formatted_time = (
        payload.preferred_time.strftime("%I:%M %p") 
        if payload.preferred_time else "your preferred time"
    )

    context = {
        "name": payload.name,
        "subject": payload.subject or "General Consultation",
        "preferred_date": formatted_date,
        "preferred_time": formatted_time,
        "unsubscribe_url": f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{email_normalized}",
        "company_profile_url": "https://vibhoospropcare.com/vibhoos_propcare_company_profile.pdf",
        "sop_url": "https://vibhoospropcare.com/vibhoos_propcare_standard_operating_procedures.pdf",
        "service_portfolio": "https://www.vibhoospropcare.com/services",
        "comment": payload.comment or "-",
    }

  

    send_email_task.delay(
        subject="Your Consultation Request - Vibhoos PropCare",
        to_email=email_normalized,
        template_name="/general/consultation_email.html",
        context=context,
        header="Consultation Request"
    )

    # ✅ 5. Response
    return {
        "message": "Consultation booked successfully — confirmation email sent!",
        "id": record.id,
    }




