from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.controllers.auth.utils import get_is_pd_filled
from jose import JWTError
from datetime import datetime, timedelta

from app.user.controllers.auth.utils import get_current_user
from app.core.services.s3 import generate_cloudfront_presigned_url,check_object_exists,upload_image_as_png
from app.core.services.db import get_db
from app.core.services.redis import redis_delete_data
from app.user.controllers.auth.main import logout
from app.user.validators.profile_update_form import ProfileUpdateForm
# from app.user.validators.forms import get_personal_details
from app.user.models.users import UserNameUpdate
from app.core.models.property_details import PropertyDetails
from app.user.models.personal_details import PersonalDetails

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
profile = APIRouter(prefix="/profile", tags=["profile"])








@profile.get("/check-username/{username}")
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

@profile.get("/check-contact/{phonenumber}")
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

@profile.get("/edit-profile")
async def get_edit_profile_details(
    response: Response,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        # Fetch personal details
        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        data = result.scalar_one_or_none()

        if not data:
            await logout(response, token, db)
            raise HTTPException(status_code=404, detail="Personal details not found")

        # Check username update constraints
        result = await db.execute(
            select(UserNameUpdate).where(UserNameUpdate.user_id == user.user_id).limit(1)
        )
        username_update = result.scalar_one_or_none()

        is_username_changable = True
        if username_update:
            last_updated = username_update.last_updated
            delta = datetime.now(tz=last_updated.tzinfo) - last_updated
            if delta <= timedelta(days=30):
                is_username_changable = False

        # Profile photo — CloudFront Signed URL
        s3_key = f"user/{user.user_id}/profile_photo/profile_photo.png"
        exists = await check_object_exists(s3_key)

        image_url = (
            await generate_cloudfront_presigned_url(s3_key)
        )

        # Final response
        return {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email": user.email,
            "user_name": data.user_name,
            "contact_number": data.contact_number,
            "house_number": data.house_number,
            "street": data.street,
            "city": data.city,
            "state": data.state,
            "pin_code": data.pin_code,
            "country": data.country,
            "image_url": image_url,
            "aadhaar_number": data.aadhaar_number,
            "pan_number": data.pan_number,
            "can_change_username": is_username_changable
        }

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))




@profile.put("/user-profile-update")
async def update_profile(
    form: ProfileUpdateForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        cache_key = f"user:{user.user_id}:personal-data"


        data = form.dict(exclude_none=True)  # Only valid fields

        if not data:
            raise HTTPException(status_code=400, detail="No valid fields to update.")

        updates = {}

        for field, value in data.items():
            if isinstance(value, str):
                value = value.strip()

            setattr(user, field, value)
            updates[field] = value

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Clear redis cache
        await redis_delete_data(cache_key)

        return {
            "message": "Profile updated successfully.",
            "updated_fields": updates
        }

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print("Update profile error:", e)
        raise HTTPException(status_code=500, detail=str(e))



@profile.put("/change-profile-photo")
async def change_profile_photo(profile_photo: UploadFile = File(...), token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(token, db)
        file_data = await profile_photo.read()
        result = await upload_image_as_png(file={"bytes": file_data}, category="profile_photo", user_id=user.user_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return result
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))
    

@profile.get("/get-subscription-details")
async def get_subscription_details(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Get subscription details for all user's properties.
    Grouped by subscription type (if available) or active status.
    """
    try:
        # 1️⃣ Validate token
        user = await get_current_user(token, db)

        # 2️⃣ Fetch user's properties
        result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.user_id == user.user_id)
        )
        properties = result.scalars().all()

        if not properties:
            raise HTTPException(status_code=404, detail="No properties found for this user")

        # 3️⃣ Separate active/inactive
        active_properties = [p for p in properties if p.active_sub]
        inactive_properties = [p for p in properties if not p.active_sub]

        # 4️⃣ Build structured response
        response = []

        if active_properties:
            response.append({
                "plan_type": "Active Subscription",
                "property_covered": [
                    {
                        "property_name": p.property_name,
                        "property_id": p.property_id,
                        "location": f"{p.city}, {p.state}",
                        "property_type": p.type,
                        "created_at": p.created_at.isoformat()
                    }
                    for p in active_properties
                ]
            })

        if inactive_properties:
            response.append({
                "plan_type": "No Active Subscription",
                "property_covered": [
                    {
                        "property_name": p.property_name,
                        "property_id": p.property_id,
                        "location": f"{p.city}, {p.state}",
                        "property_type": p.type.upper(),
                        "created_at": p.created_at.isoformat()
                    }
                    for p in inactive_properties
                ]
            })

        return response

    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching subscription details: {str(e)}")

















@profile.get('/user-registration-status')
async def user_registration_status(token: str = Depends(oauth2_scheme)):
    try:
        return {"is_pdfilled": get_is_pd_filled(token)}
    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching subscription details: {str(e)}")





async def get_user_id(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    try:
        user=await get_current_user(token,db)
        return user.user_id
    except HTTPException as e:
        raise e
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching subscription details: {str(e)}")




@profile.get('/get-personal-data')
async def get_personal_data(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Authenticate User
        user = await get_current_user(token, db)

        # 2. Fetch personal details
        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Personal details not found")

        # 3. Prepare response data
        data = {
            "full_name": f"{record.first_name} {record.last_name}",
            "user_name": record.user_name,
            "profile_photo_url": record.profile_photo_url,
            "contact_number": record.contact_number,
            "location": record.location,
            "member_from": record.member_from,
            "total_properties": record.total_properties,
            "with_plans": record.with_plans,
            "no_plans": record.no_plans,
            "nri": record.nri
        }

        return data

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching personal details: {str(e)}"
        )
