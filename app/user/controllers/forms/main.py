from fastapi import APIRouter,Depends,HTTPException,status
from jose import JWTError
from app.user.validators.forms import get_personal_details
from app.core.controllers.auth.main import oauth2_scheme
from app.user.models.personal_details import PersonalDetails
from app.core.models import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.user.models.personal_details import PersonalDetails
from app.core.controllers.auth.utils import  get_current_user
from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.models.personal_details import PersonalDetails
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

form=APIRouter(prefix="/form",tags=['form'])



@form.post("/submit-details")
async def submit(
    data: dict = Depends(get_personal_details),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        current_user = await get_current_user(token, db)
        current_user_id = current_user.user_id  

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

        current_user.is_pdfilled = True

        db.add(user)
        db.add(current_user)  
        await db.commit()
        await db.refresh(user)
        await db.refresh(current_user)

        return {
            "message": "Data received and processed successfully",
            "user_id": current_user_id
        }

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required field: {e.args[0]}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@form.get("/check-username/{username}")
async def check_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Decode token to ensure it's valid
        payload = await get_current_user(token,db)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Now query the DB
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_name == username))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return {"available": True}

@form.get("/check-contact/{phonenumber}")
async def check_phonenumber(
    phonenumber: str,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Decode token to ensure it's valid
        payload = await get_current_user(token,db)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Now query the DB
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.contact_number == phonenumber))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="phone_number  already exists")
    
    return {"available": True}
