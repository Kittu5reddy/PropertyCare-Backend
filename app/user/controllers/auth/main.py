
from fastapi import HTTPException,Depends,APIRouter
from fastapi.responses import JSONResponse,HTMLResponse
from app.core.services.db import get_db
from sqlalchemy.ext.asyncio import (
    AsyncSession
)
from app.core.business_logic.ids import generate_user_id
from config import settings
from sqlalchemy import select,desc
from app.user.models.users import User
from app.core.controllers.auth import REFRESH_TOKEN_EXPIRE_DAYS,BASE_USER_URL,FORGOT_PASSWORD_TIME_LIMIT
from app.core.controllers.auth.utils import (create_access_token,
                                             create_refresh_token,
                                             get_password_hash,
                                             verify_password,
                                             verify_refresh_token
)
from app.user.validators.auth import User as LoginSchema 

from .utils import get_user_by_email,create_verification_token,get_current_user,get_is_pd_filled
from app.user.controllers.emails.main import send_verification_email,send_forgot_password_email
from app.core.validators.forgotpassword import ForgotPasswordRequest,ResetPasswordRequest
from datetime import datetime,timedelta
# from 
from app.user.models.personal_details import PersonalDetails
from app.core.services.redis import redis_set_data,redis_get_data,redis_delete_data,redis_client
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.services.s3 import create_user_directory

from app.user.validators.auth import ChangePassword


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth=APIRouter(prefix='/auth',tags=['auth'])
#=========================
#       POST ROUTES
#=========================

@auth.post("/login")
async def login(user: LoginSchema, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
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
    
    send_forgot_password_email( user.email, reset_link,context)

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
    

from fastapi import Request,Response


@auth.post("/refresh")
async def refresh_token(request: Request):
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






# #=========================
# #        PUT ROUTES
# #=========================

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



