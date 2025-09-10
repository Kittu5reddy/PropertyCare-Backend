from app.user.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash,verify_refresh_token,get_current_user,get_current_user_personal_details,verify_password,get_is_pd_filled
from app.user.controllers.auth.email import create_verification_token,send_verification_email
from fastapi import APIRouter,Request,status
from app.user.controllers.auth.utils import get_user_by_email,REFRESH_TOKEN_EXPIRE_DAYS,generate_user_id
from app.user.validators.auth import User as LoginSchema 
from app.user.models.users import User,UserNameUpdate
from app.user.models.personal_details import PersonalDetails
from fastapi import APIRouter, HTTPException,Depends,BackgroundTasks
from app.user.controllers.forms.utils import create_user_directory
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from fastapi.responses import HTMLResponse
from fastapi import Response
from passlib.context import CryptContext
from app.user.models import get_db,AsyncSession,redis_set_data,redis_get_data,redis_update_data,redis_delete_data,redis_client
from fastapi import Depends,File,UploadFile
from sqlalchemy import select, desc
from fastapi import BackgroundTasks
from app.user.validators.auth import ChangePassword
from app.user.validators.user_profile import ChangeFirstName,ChangeLastName,ChangeUsername,ChangeContactNumber,ChangeHouseNumber,ChangeStreet,ChangeCity,ChangeState,ChangeCountry,ChangePinCode
from app.user.controllers.forms.utils import get_image,get_current_time
from datetime import datetime,timedelta
from app.user.controllers.forms.utils import upload_image_as_png
import time
auth=APIRouter(prefix='/auth',tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.responses import JSONResponse




#=========================
#       POST ROUTES
#=========================

@auth.post("/login")
async def login(user: LoginSchema, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_verified:
        if not db_user.verification_token:
            db_user.verification_token = create_verification_token()
            await db.commit()
            await db.refresh(db_user)
        background_tasks.add_task(send_verification_email, db_user.email, db_user.verification_token)
        raise HTTPException(status_code=403, detail="Email not verified. A new verification email has been sent.")

    payload = {"sub": user.email, "is_pdfilled": db_user.is_pdfilled}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    
    response = JSONResponse(content={"message": "Login successful", "access_token": access_token, "token_type": "Bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60*60*24*REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth/refresh"
    )
    return response


@auth.post("/signup")
async def signup(user: LoginSchema, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(user.password)
    token = create_verification_token()

    result = await db.execute(select(User).order_by(desc(User.id)).limit(1))
    last_user = result.scalar_one_or_none()
    next_id = last_user.id + 1 if last_user else 1
    user_id = generate_user_id(next_id)

    new_user = User(user_id=user_id, email=user.email, hashed_password=hashed_password,
                    verification_token=token, is_verified=False)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    background_tasks.add_task(send_verification_email, new_user.email, new_user.verification_token)

    return {"message": "User created successfully. Please check your email to verify your account.", "email": new_user.email}


@auth.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    payload = verify_refresh_token(refresh_token)
    access_token = create_access_token(payload)
    return {"access_token": access_token, "type": "Bearer"}


@auth.post("/logout")
async def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)

    # Find and delete all cache keys for this user
    pattern = f"user:{user.user_id}:*"
    keys = await redis_client.keys(pattern)  # gets all matching keys
    if keys:
        await redis_client.delete(*keys)

    # Remove refresh token cookie
    response.delete_cookie("refresh_token")

    return {"message": "Logged out"}



#=========================
#        GET ROUTES
#=========================

@auth.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()
    
    if not user:
        return HTMLResponse(
            content="<h2>Invalid or expired token</h2><p>Please check your verification link or try signing up again.</p>",
            status_code=400
        )
    if user.is_verified:
        return HTMLResponse(
            content="<h2>Email already verified</h2><p>You can now log in to your account.</p>",
            status_code=200
        )
    user.is_verified = True
    user.verification_token = None
    await db.commit()
    await create_user_directory(user.user_id)

    return HTMLResponse(
        content='<h2>Email verification successful</h2><p>Your email has been verified. You can now log in to your account.</p>'
                '<a href="https://propertycare-nine.vercel.app/login">Click Here</a>',
        status_code=200
    )


@auth.get('/user-registration-status')
async def user_registration_status(token: str = Depends(oauth2_scheme)):
    try:
        return {"is_pdfilled": get_is_pd_filled(token)}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@auth.get("/get-user-id")
async def get_user_id(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.user_id}


@auth.get("/get-personal-data")
async def get_personal_details(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    cache_key=f"user:{user.user_id}:personal-data"
    cache_data=await redis_get_data(cache_key)
    if cache_data:
        print("hit")
        # print(cache_data)
        return cache_data
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_id == user.user_id))
    data = result.scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404, detail="Personal details not found")

    profile_url = get_image(f"/user/{user.user_id}/profile_photo/profile_photo.png{get_current_time()}")
    data= {
        "full_name": f"{data.first_name} {data.last_name}",
        "user_name": data.user_name,
        "contact_number": data.contact_number,
        "location": f"{data.city}, {data.state}",
        "member_from":  data.created_at.isoformat(),
        "total_properties": 200,
        "with_plans": 20,
        "no_plans": 180,
        "profile_photo_url": profile_url
    }
    await redis_set_data(cache_key,data)
    return data


@auth.get('/get-subscription-details')
async def get_subscription_details(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    return [
        {
            "plan_type": "Basic",
            "property_covered": [
                {"property_name": "Ramanthapur House", "property_id": "1010101", "location": "Hyderabad", "property_type": "Residential"},
                {"property_name": "Kukatpally Flat", "property_id": "1010102", "location": "Hyderabad", "property_type": "Apartment"}
            ]
        },
        {
            "plan_type": "Premium",
            "property_covered": [
                {"property_name": "Jubilee Hills Villa", "property_id": "2020202", "location": "Hyderabad", "property_type": "Villa"},
                {"property_name": "Madhapur Studio", "property_id": "2020203", "location": "Hyderabad", "property_type": "Studio"}
            ]
        }
    ]


@auth.get("/edit-profile")
async def get_edit_profile_details(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_id == user.user_id))
    data = result.scalar_one_or_none()
    if not data:
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
        "country": data.country,
        "image_url": get_image(f"/user/{user.user_id}/profile_photo/profile_photo.png{get_current_time()}"),
        "aadhaar_number": data.aadhaar_number,
        "pan_number": data.pan_number,
        "can_change_username": is_username_changable
    }



#=========================
#        PUT ROUTES
#=========================

@auth.put("/change-password")
async def change_password(payload: ChangePassword, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Wrong password")
    user.hashed_password = get_password_hash(payload.new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Password changed successfully"}


@auth.put('/change-first-name')
async def change_first_name(form: ChangeFirstName, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.first_name = form.first_name.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "First name updated successfully."}


@auth.put('/change-last-name')
async def change_last_name(form: ChangeLastName, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.last_name = form.last_name.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Last name updated successfully."}


@auth.put('/change-username')
async def change_username(form: ChangeUsername, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    existing_username = await db.execute(select(PersonalDetails).where(PersonalDetails.user_name == form.user_name))
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    personal_details_result = await db.execute(select(PersonalDetails).where(PersonalDetails.user_id == user.user_id))
    personal_details = personal_details_result.scalar_one_or_none()
    personal_details.user_name = form.user_name
    db.add(personal_details)
    await db.commit()
    await db.refresh(personal_details)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Username updated successfully."}


@auth.put('/change-contact-number')
async def change_contact_number(form: ChangeContactNumber, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalDetails).where(PersonalDetails.contact_number == form.contact_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Number already exists")

    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.contact_number = form.contact_number.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Contact number updated successfully."}


@auth.put('/change-house-number')
async def change_house_number(form: ChangeHouseNumber, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.house_number = form.house_number.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "House number updated successfully."}


@auth.put("/change-profile-photo")
async def change_profile_photo(profile_photo: UploadFile = File(...), token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = await get_current_user(token, db)
    file_data = await profile_photo.read()
    result = await upload_image_as_png(file={"bytes": file_data}, category="profile_photo", user_id=user.user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return result


@auth.put('/change-street')
async def change_street(form: ChangeStreet, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.street = form.street.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Street updated successfully."}


@auth.put('/change-city')
async def change_city(form: ChangeCity, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.city = form.city.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "City updated successfully."}


@auth.put('/change-state')
async def change_state(form: ChangeState, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.state = form.state.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "State updated successfully."}


@auth.put('/change-pin-code')
async def change_pin_code(form: ChangePinCode, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.pin_code = form.pin_code
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Pin code updated successfully."}


@auth.put('/change-country')
async def change_country(form: ChangeCountry, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user: PersonalDetails = await get_current_user_personal_details(token, db)
    user.country = form.country.strip()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    cache_key=f"user:{user.user_id}:personal-data"
    await redis_delete_data(cache_key)
    return {"message": "Country updated successfully."}
