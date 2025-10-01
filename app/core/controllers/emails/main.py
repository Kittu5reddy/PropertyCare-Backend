from fastapi import APIRouter,Depends
from app.core.validators.emails import NewsLetter as NewsLetterSchema
from app.core.models.newsletter import NewsLetter 
from app.core.models.consultation import Consultation  
from app.core.validators.consultation import Consultation as ConsultationSchema
from .utils import send_consultation_email,send_newsletter_email
email=APIRouter(prefix="/email",tags=['emails'])
from sqlalchemy import select
from app.core.models import get_db,AsyncSession


@email.post('/subscribe-news-letters')
async def news_letter_subscribe(payload: NewsLetterSchema, db: AsyncSession = Depends(get_db)):
    data = await db.execute(select(NewsLetter).where(NewsLetter.email == payload.email).limit(1))
    isavailable = data.scalar_one_or_none()

    if not isavailable:
        record = NewsLetter(email=payload.email)
        db.add(record)
        await db.commit()
        await db.refresh(record)

        # Send newsletter email
        unsubscribe_url = f"https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{payload.email}"
        send_newsletter_email(payload.email, unsubscribe_url)

        return {"message": "subscribed successfully"}
    else:
        if not isavailable.status:
            isavailable.status=True
            db.add(record)
            await db.commit()
            await db.refresh(record)
        return {"message": "already subscribed"}



from fastapi.responses import HTMLResponse

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
    <a href="/" style="color: #0C4A6E; text-decoration: none;">Back to Home</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_not_found, status_code=404)


@email.post('/book-consulting')
async def booking_consulting(
    payload: ConsultationSchema, 
    db: AsyncSession = Depends(get_db)
):
    record = Consultation(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time,
        reason_for_consultation=payload.reason_for_consultation
    )
    
    db.add(record)
    await db.commit()
    await db.refresh(record)

    send_consultation_email(
        name=payload.name,
        email=payload.email,
        preferred_date=payload.preferred_date,
        preferred_time=payload.preferred_time
    )

    return {"message": "consultation booked successfully", "id": record.id}