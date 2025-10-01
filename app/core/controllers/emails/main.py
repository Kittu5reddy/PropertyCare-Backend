from fastapi import APIRouter,Depends
from app.core.validators.emails import NewsLetter as NewsLetterSchema
from app.core.models.newsletter import NewsLetter 
from app.core.models.consultation import Consultation  
from app.core.validators.consultation import Consultation as ConsultationSchema 
email=APIRouter(prefix="/email",tags=['emails'])
from sqlalchemy import select
from app.core.models import get_db,AsyncSession

@email.post('/subscribe-news-letters')
async def news_letter_subscribe(payload:NewsLetterSchema,db:AsyncSession=Depends(get_db)):
    data=await db.execute(select(NewsLetter).where(NewsLetter.email==payload.email).limit(1))
    isavailable=data.scalar_one_or_none()
    if not isavailable:
        record=NewsLetter(email=payload.email)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {"message":"subscribed succesfully"}
    else:
        return {"message":"already subscribed"}
    


@email.get('/unsubscribe-news-letters/{email}')
async def unsubscribe_news_letter(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NewsLetter).where(NewsLetter.email == email).limit(1)
    )
    record = result.scalar_one_or_none()

    if record:
        record.status = False  # Make sure NewsLetter model has a "status" column
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {"message": "unsubscribed successfully"}

    return {"message": "email not found"}





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
    return {"message": "consultation booked successfully", "id": record.id}