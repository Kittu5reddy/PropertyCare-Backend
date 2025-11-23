from app.core.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash,verify_refresh_token,get_current_user,get_current_user_personal_details,verify_password,BASE_USER_URL,FORGOT_PASSWORD_TIME_LIMIT,get_is_pd_filled
from app.user.controllers.emails.utils import create_verification_token,send_verification_email,send_forgot_password_email
from fastapi import APIRouter,Request
from app.user.controllers.forms.utils import check_object_exists,list_s3_objects,generate_cloudfront_presigned_url
from app.core.controllers.auth.utils import get_user_by_email,REFRESH_TOKEN_EXPIRE_DAYS,generate_user_id
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
from app.core.models import get_db,AsyncSession,redis_set_data,redis_get_data,redis_delete_data,redis_client
from fastapi import Depends,File,UploadFile
from sqlalchemy import select, desc
from fastapi import BackgroundTasks
from app.user.validators.auth import ChangePassword
from app.user.validators.user_profile import ChangeFirstName,ChangeLastName,ChangeUsername,ChangeContactNumber,ChangeHouseNumber,ChangeStreet,ChangeCity,ChangeState,ChangeCountry,ChangePinCode
from app.user.controllers.forms.utils import get_image,get_current_time
from datetime import datetime,timedelta
from app.user.controllers.forms.utils import upload_image_as_png
import time
from app.core.validators.forgotpassword import ForgotPasswordRequest,ResetPasswordRequest
from app.core.models.property_details import PropertyDetails
from config import settings
from app.user.validators.personal_details import  PersonalDetails as PersonalDetailSchema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth=APIRouter(prefix='/auth',tags=['auth'])


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.responses import JSONResponse




#=========================
#       POST ROUTES
#=========================

@auth.post("/login")
async def login(user: LoginSchema, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_verified:
        if not db_user.verification_token:
            db_user.verification_token = create_verification_token()
            await db.commit()
            await db.refresh(db_user)
        
        send_verification_email(email=db_user.email,token=db_user.verification_token)
        
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
async def signup(user: LoginSchema,  db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(user.password)
    token = create_verification_token()

    result = await db.execute(select(User).order_by(desc(User.id)).limit(1))
    last_user = result.scalar_one_or_none()
    next_id = last_user.id + 1 if last_user else 1
    user_id = generate_user_id(next_id+int(settings.USERS_STARTING_NUMBER))

    new_user = User(user_id=user_id, email=user.email, hashed_password=hashed_password,
                    verification_token=token, is_verified=False)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    send_verification_email(new_user.email,new_user.verification_token)

    return {"message": "User created successfully. Please check your email to verify your account.", "email": new_user.email}






# ===== 1️⃣ Forgot Password - Send Email =====
@auth.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data=await db.execute(select(PersonalDetails).where(user.user_id==PersonalDetails.user_id).limit(1))
    data=data.scalar_one_or_none()
    # Generate token and store in Redis
    token = create_verification_token()
    cache_key = f"user:forgot-password:{user.email}"
    await redis_set_data(cache_key, token, FORGOT_PASSWORD_TIME_LIMIT)

    # Send Email (background)
    reset_link = f"{BASE_USER_URL}/reset-password/{user.email}/{token}"
    context={
        "reset_link":reset_link,
        "current_year" : datetime.now().year,
        "name":data.first_name+data.last_name if data else "None"
    }
    
    background_tasks.add_task(send_forgot_password_email, user.email, reset_link,context)

    return {"message": "Password reset link sent to your email"}


# ===== 2️⃣ Reset Password =====
@auth.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        cache_key = f"user:forgot-password:{payload.email}"
        stored_token = await redis_get_data(cache_key)

        if not stored_token:
            raise HTTPException(status_code=400, detail="Token expired or invalid")

        if stored_token != payload.token:
            raise HTTPException(status_code=400, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update password
        user.hashed_password = get_password_hash(payload.new_password)
        db.add(user)
        await db.commit()

        # Clear token and user cache
        await redis_delete_data(cache_key)
        await redis_delete_data(f"user:{user.user_id}:personal-data")

        return {"message": "Password reset successful"}

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))
    




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
    try:
        # 1️⃣ Find user with matching verification token
        result = await db.execute(select(User).where(User.verification_token == token))
        user = result.scalar_one_or_none()

        # 2️⃣ Invalid or expired token
        if not user:
            return HTMLResponse(
                content="""
                <div style='font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 40px; text-align: center; height: 100vh; display: flex; align-items: center; justify-content: center;'>
                    <div style='max-width: 500px; background: #fff; padding: 35px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 6px solid #dc2626;'>
                        <h2 style='color: #dc2626;'>Invalid or Expired Token</h2>
                        <p style='color: #374151;'>Please check your verification link or try signing up again.</p>
                    </div>
                </div>
                """,
                status_code=400
            )

        # 3️⃣ If already verified
        if user.is_verified:
            return HTMLResponse(
                content=f"""
                <div style='font-family: Arial, sans-serif; background-color: #f3f4f6; padding: 40px; text-align: center; height: 100vh; display: flex; align-items: center; justify-content: center;'>
                    <div style='max-width: 500px; background: #fff; padding: 35px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 6px solid #16a34a;'>
                        <h2 style='color: #16a34a;'>Email Already Verified</h2>
                        <p style='color: #374151;'>You can now log in to your account.</p>
                        <a href="{settings.BASE_USER_URL}/login"
                           style='display:inline-block;margin-top:15px;background-color:#16a34a;color:#fff;padding:12px 24px;
                                  text-decoration:none;border-radius:6px;font-weight:bold;'>
                            Go to Login
                        </a>
                    </div>
                </div>
                """,
                status_code=200
            )

        # 4️⃣ Update user verification
        user.is_verified = True
        user.verification_token = None
        await db.commit()

        # Create user directory for uploads, etc.
        await create_user_directory(user.user_id)

        # 5️⃣ Return success HTML
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Email Verification - Vibhoos PropCare</title>
    <style>
      body {{
        margin: 0;
        padding: 0;
        font-family: "Segoe UI", Roboto, Arial, sans-serif;
        height: 100vh;
        background: linear-gradient(135deg, #e8f5e9, #f1fdf4);
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .container {{
        width: 100%;
        max-width: 520px;
        background: #ffffff;
        padding: 40px 35px;
        border-radius: 16px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
        border-top: 6px solid #16a34a;
        text-align: center;
        transition: all 0.3s ease-in-out;
      }}
      .logo {{
        width: 130px;
        margin-bottom: 20px;
      }}
      h2 {{
        color: #166534;
        font-size: 26px;
        margin-bottom: 12px;
      }}
      p {{
        color: #374151;
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 25px;
      }}
      a.button {{
        display: inline-block;
        background: linear-gradient(90deg, #16a34a, #22c55e);
        color: white;
        padding: 12px 28px;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 3px 8px rgba(34, 197, 94, 0.4);
        transition: background 0.3s ease, transform 0.2s ease;
      }}
      a.button:hover {{
        background: linear-gradient(90deg, #22c55e, #16a34a);
        transform: scale(1.03);
      }}
      .footer-text {{
        margin-top: 25px;
        font-size: 13px;
        color: #6b7280;
      }}
      .footer-text a {{
        color: #16a34a;
        text-decoration: none;
        font-weight: 500;
      }}
      footer {{
        position: absolute;
        bottom: 20px;
        text-align: center;
        width: 100%;
        color: #9ca3af;
        font-size: 12px;
      }}
      @media (max-width: 600px) {{
        .container {{
          margin: 0 15px;
          padding: 30px 20px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <img
        src="https://vibhoospropcare.com/logo.png"
        alt="Vibhoos PropCare"
        class="logo"
      />
      <h2>Email Verified Successfully!</h2>
      <p>
        Great news! 🎉 Your email has been verified successfully.<br />
        You can now log in and explore your
        <b>Vibhoos PropCare</b> account.
      </p>
      <a href="{settings.BASE_USER_URL}/login" class="button">Go to Login</a>

      <p class="footer-text">
        Need help? Contact our support team at
        <a href="mailto:support@vibhoospropcare.com">
          support@vibhoospropcare.com
        </a>
      </p>
    </div>
    <footer>© 2025 Vibhoos PropCare. All rights reserved.</footer>
  </body>
</html>
""",
            status_code=200
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email verification failed: {str(e)}")






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
async def get_personal_details(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 1️⃣ Validate user
        user = await get_current_user(token, db)

        cache_key = f"user:{user.user_id}:personal-data"

        # 2️⃣ Check Redis
        cache_data = await redis_get_data(cache_key)
        if cache_data:
            print("Cache hit ✅")
            return cache_data

        # 3️⃣ Personal details
        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        data = result.scalar_one_or_none()
        if not data:
            raise HTTPException(status_code=404, detail="Personal details not found")

        # 4️⃣ Property details
        properties_result = await db.execute(
            select(PropertyDetails).where(PropertyDetails.user_id == user.user_id)
        )
        property_data = properties_result.scalars().all()
        total_properties = len(property_data)

        # 5️⃣ Active subscriptions
        active_result = await db.execute(
            select(PropertyDetails).where(
                PropertyDetails.user_id == user.user_id,
                PropertyDetails.active_sub == True
            )
        )
        with_plans = len(active_result.scalars().all())
        no_plans = total_properties - with_plans

        # 6️⃣ Profile photo logic (CloudFront)
        s3_key = f"user/{user.user_id}/profile_photo/profile_photo.png"
        exists = await check_object_exists(s3_key)

        profile_url = (
            await generate_cloudfront_presigned_url(s3_key)
        )

        # 7️⃣ Build response
        response = {
            "full_name": f"{data.first_name} {data.last_name}",
            "user_name": data.user_name,
            "contact_number": data.contact_number,
            "location": f"{data.city}, {data.state}",
            "member_from": data.created_at.isoformat(),
            "total_properties": total_properties,
            "with_plans": with_plans,
            "no_plans": no_plans,
            "profile_photo_url": profile_url,
        }

        # 8️⃣ Cache response
        await redis_set_data(cache_key, response)

        return response

    except Exception as e:
        print(f"❌ Error in get_personal_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@auth.get("/get-subscription-details")
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


@auth.get("/edit-profile")
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



#=========================
#        PUT ROUTES
#=========================

@auth.put("/change-password")
async def change_password(payload: ChangePassword, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
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
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))



@auth.put('/change-first-name')
async def change_first_name(form: ChangeFirstName, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.first_name = form.first_name.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "First name updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-last-name')
async def change_last_name(form: ChangeLastName, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.last_name = form.last_name.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "Last name updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-username')
async def change_username(form: ChangeUsername, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
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
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-contact-number')
async def change_contact_number(form: ChangeContactNumber, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
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
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-house-number')
async def change_house_number(form: ChangeHouseNumber, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.house_number = form.house_number.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "House number updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put("/change-profile-photo")
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

@auth.put('/change-street')
async def change_street(form: ChangeStreet, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.street = form.street.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "Street updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-city')
async def change_city(form: ChangeCity, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.city = form.city.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "City updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-state')
async def change_state(form: ChangeState, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.state = form.state.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "State updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-pin-code')
async def change_pin_code(form: ChangePinCode, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.pin_code = form.pin_code
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "Pin code updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))

@auth.put('/change-country')
async def change_country(form: ChangeCountry, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.country = form.country.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        cache_key=f"user:{user.user_id}:personal-data"
        await redis_delete_data(cache_key)
        return {"message": "Country updated successfully."}
    except HTTPException as e:
        raise e 
    except JWTError as e:
        raise HTTPException(status_code=401,detail="Token Expired")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail=str(e))
    






# @auth.post('/add-user-details')
# async def add_user_details(payload:PersonalDetailSchema,
#                            token:str=Depends(oauth2_scheme),
#                            db:AsyncSession=Depends(get_db)):
#     try:
#         user=await get_current_user(token,db)
#         is_exist_smt=await db.execute(select(PersonalDetails).where(PersonalDetails.user_id==user.user_id))
#         is_exist= is_exist_smt.scalar_one_or_none()
#         if is_exist:
#             user_record_txt=await db.execute(select(User).where(User.user_id==user.user_id))
#             user_record=user_record_txt.scalar_one_or_none()
#             user_record.is_pdfilled=True
#             db.add(user_record)
#             await db.commit()
#             await db.refresh(user_record)
#             raise HTTPException(status_code=400,detail="Record Already exist")
#         new_record=PersonalDetails(**payload)
#     except:


from app.user.controllers.forms.utils import upload_documents,upload_image_as_png


@auth.post('/add-user-details')
async def add_user_details(
    payload: PersonalDetailSchema,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        # ✔ Check if already exists
        existing_record_stmt = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        existing_record = existing_record_stmt.scalar_one_or_none()

        if existing_record:
            # Update user table
            user_record_txt = await db.execute(select(User).where(User.user_id == user.user_id))
            user_record = user_record_txt.scalar_one_or_none()
            user_record.is_pdfilled = True

            db.add(user_record)
            await db.commit()
            await db.refresh(user_record)

            raise HTTPException(status_code=400, detail="Record already exists")

        # ✔ Convert Pydantic → dict
        data = payload.dict()

        # ✔ Add user_id manually
        data["user_id"] = user.user_id

        # ✔ Create SQLAlchemy instance
        new_record = PersonalDetails(**data)

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        return {"message": "Personal details added successfully"}

    except Exception as e:
        raise
    except Exception as e:
        print(str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    




@auth.post("/add-user-documents")
async def add_user_documents(
    pan_file: UploadFile | None = File(None),
    aadhar_file: UploadFile | None = File(None),
    profile_photo: UploadFile | None = File(None),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        stmt = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        personal_details = stmt.scalar_one_or_none()

        if not personal_details:
            raise HTTPException(
                status_code=400, detail="Please complete personal details first."
            )

        # NRI user cannot upload PAN or Aadhar (but CAN upload profile photo)
        if personal_details.nri and (pan_file or aadhar_file):
            raise HTTPException(
                status_code=400,
                detail="NRI users cannot upload PAN or Aadhaar documents."
            )

        # Convert UploadFile to dict only if file is provided
        async def to_dict(f: UploadFile) -> dict:
            return {
                "filename": f.filename,
                "bytes": await f.read(),
                "content_type": f.content_type or "application/octet-stream"
            }

        uploaded_files = {}

        # Upload profile photo if provided
        if profile_photo is not None:
            profile_dict = await to_dict(profile_photo)
            profile_url = await upload_image_as_png(
                profile_dict, "profile_photo", user.user_id
            )

            if "error" in profile_url:
                raise HTTPException(status_code=500, detail="Profile upload failed")

            personal_details.profile_photo = profile_url["file_path"]
            uploaded_files["profile_photo"] = profile_url["file_path"]

        # Upload PAN if provided
        if pan_file is not None:
            pan_dict = await to_dict(pan_file)
            pan_url = await upload_documents(pan_dict, "pan", user.user_id)

            if "error" in pan_url:
                raise HTTPException(status_code=500, detail="PAN upload failed")

            personal_details.pan_document = pan_url["file_path"]
            uploaded_files["pan_document"] = pan_url["file_path"]

        # Upload Aadhaar if provided
        if aadhar_file is not None:
            aadhar_dict = await to_dict(aadhar_file)
            aadhar_url = await upload_documents(aadhar_dict, "aadhaar", user.user_id)

            if "error" in aadhar_url:
                raise HTTPException(status_code=500, detail="Aadhaar upload failed")

            personal_details.aadhaar_document = aadhar_url["file_path"]
            uploaded_files["aadhaar_document"] = aadhar_url["file_path"]

        # SAVE TO DB
        db.add(personal_details)
        await db.commit()
        await db.refresh(personal_details)

        return {
            "message": "Documents uploaded successfully",
            "uploaded": uploaded_files
        }

    except Exception as e:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@auth.get("/check-username/{username}")
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





@auth.get("/check-contact/{phonenumber}")
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
