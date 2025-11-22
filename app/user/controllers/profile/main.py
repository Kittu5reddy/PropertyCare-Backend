from fastapi import Depends,HTTPException,APIRouter
from app.core.controllers.auth.utils import get_current_user,get_current_user_personal_details
from app.user.validators.profile_update_form import ProfileUpdateForm
from app.user.models.users import UserNameUpdate
from app.user.models.personal_details import PersonalDetails
from jose import JWTError
from fastapi import Response
from app.core.models import get_db,AsyncSession,redis_delete_data
from fastapi import Depends,File,UploadFile
from sqlalchemy import select
from app.user.controllers.forms.utils import get_image,get_current_time
from datetime import datetime,timedelta
from app.user.controllers.forms.utils import upload_image_as_png
from app.core.controllers.auth.main import oauth2_scheme
profile=APIRouter(prefix="/profile",tags=['profile'])




@profile.get("/edit-profile")
async def get_edit_profile_details(response:Response,token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(token, db)
        result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_id == user.user_id))
        data = result.scalar_one_or_none()
        if not data:
            # await logout(response,token,db)
            raise HTTPException(status_code=404, detail="Personal details not found")

        result = await db.execute(select(UserNameUpdate).where(UserNameUpdate.user_id == user.user_id).limit(1))
        username_update = result.scalar_one_or_none()

        is_username_changable = True
        if username_update:
            last_updated = username_update.last_updated
            delta = datetime.now(tz=last_updated.tzinfo) - last_updated
            if delta <= timedelta(days=30):
                is_username_changable = False

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
            "is_nri":data.nri,
            "country": data.country,
            "image_url": get_image(f"/user/{user.user_id}/profile_photo/profile_photo.png{get_current_time()}"),
            "aadhaar_number": data.aadhaar_number,
            "pan_number": data.pan_number,
            "can_change_username": is_username_changable
        }
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))


@profile.put("/user-profile-update")
async def update_profile(
    form: ProfileUpdateForm,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user_personal_details(token, db)
        user_id = user.user_id

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
        await redis_delete_data(f"user:{user_id}:personal-data")

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