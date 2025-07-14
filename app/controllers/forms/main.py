from fastapi import APIRouter,Depends,HTTPException
from jose import JWTError
from app.validators.forms import get_personal_details
from app.controllers.auth.main import oauth2_scheme
from app.models.personal_details import PersonalDetails
from app.models import get_db
form=APIRouter(prefix="/form",tags=['form'])
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.personal_details import PersonalDetails


from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PersonalDetails

@form.post("/submit-details")
async def submit(
    data: dict = Depends(get_personal_details),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    current_user = await get_current_user(token, db)
    current_user_id = current_user.user_id  # ✅ Fix: .user_id is a property of resolved object

    # Save user details to DB
    user = PersonalDetails(
        first_name=data["first_name"],
        last_name=data["last_name"],
        user_name=data["user_name"],
        date_of_birth=data["date_of_birth"],
        gender=data["gender"],
        contact_number=str(data["contact_number"]),
        description=data["description"],
        house_number=data["address"]["house_number"],
        street=data["address"]["street"],
        city=data["address"]["city"],
        state=data["address"]["state"],
        country=data["address"]["country"],
        pin_code=int(data["address"]["pincode"]),
        pan_number=data["govt_ids"]["pan_number"],
        aadhaar_number=data["govt_ids"]["aadhaar_number"],
        user_id=current_user_id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)  # to get auto-generated fields if any


    return {
        "message": "Data received and processed successfully",
        "user_id": current_user_id
    }


from app.controllers.auth.utils import  get_current_user

@form.get("/check-username/{username}")
async def check_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Decode token to ensure it's valid
        payload = get_current_user(token,db)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Now query the DB
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_name == username))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return {"available": True}

@form.get("/check-phonenumber/{phonenumber}")
async def check_phonenumber(
    phonenumber: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Decode token to ensure it's valid
        payload = get_current_user(token,db)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Now query the DB
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.contact_number == phonenumber))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="phone_number  already exists")
    
    return {"available": True}
