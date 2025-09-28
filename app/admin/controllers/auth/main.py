from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, Body
from app.core.models import redis_set_data, redis_get_data
from app.admin.validators.admins import AdminLogin, OTP, BlackListOTP
from .utils import (
    ADMIN_EMAILS,
    generate_otp,
    send_otp_email,
    create_access_token,
    create_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
    verify_refresh_token,
    BLACK_LIST_TIME
)

admin_auth = APIRouter(prefix="/admin-auth",tags=["admin-auth"])


# ----------------------
# ADMIN LOGIN - SEND OTP
# ----------------------
@admin_auth.post("/login")
async def admin_login(payload: AdminLogin, background_tasks: BackgroundTasks):
    email = payload.email

    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=404, detail="Email is not registered")
    blacklist_key = f"black-list:email:{email}"
    if await redis_get_data(blacklist_key):
        raise HTTPException(
                status_code=403,
                detail=f"Email is blacklisted. Wait for {BLACK_LIST_TIME} mins"
            )
    try:
        # Generate OTP and store in Redis
        otp, expire = generate_otp(email)
        cache_key = f"admin:{email}:otp"
        await redis_set_data(cache_key, otp, time=expire)

        # Send OTP asynchronously via email
        background_tasks.add_task(send_otp_email, email, otp)

        return {"message": "OTP sent to your email"}

    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


# -------------------------------
# VERIFY LOGIN - OTP & TOKEN ISSUING
# -------------------------------
@admin_auth.post("/verify-login")
async def admin_verify(payload: OTP, response: Response):
    email = payload.email
    otp = payload.otp

    try:
        # Check if email is blacklisted
        blacklist_key = f"black-list:email:{email}"
        if await redis_get_data(blacklist_key):
            raise HTTPException(
                status_code=403,
                detail=f"Email is blacklisted. Wait for {BLACK_LIST_TIME} mins"
            )

        # Fetch OTP from Redis
        otp_key = f"admin:{email}:otp"
        stored_otp = await redis_get_data(otp_key)
        if not stored_otp or stored_otp != otp:
            raise HTTPException(status_code=401, detail="Invalid or expired OTP")

        # Generate tokens
        access_token = create_access_token({"email": email})
        refresh_token = await create_refresh_token(email=email)

        # Set refresh token in secure cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return {"login": "success", "access_token": access_token}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error verifying login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --------------------------------
# REFRESH ACCESS TOKEN ENDPOINT
# --------------------------------
@admin_auth.post("/admin-refresh")
async def admin_refresh_token(response: Response, refresh_token: str = Body(...)):
    try:
        email = verify_refresh_token(refresh_token)
        if not email or email not in ADMIN_EMAILS:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Generate new access token
        access_token = create_access_token({"email": email})

        return {"access_token": access_token, "message": "Access token refreshed successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error refreshing token: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# -----------------------
# BLACKLIST ADMIN EMAIL
# -----------------------
@admin_auth.post("/black-list-admin")
async def black_list_admin(payload: BlackListOTP):
    email = payload.email
    try:
        cache_key = f"black-list:email:{email}"
        await redis_set_data(cache_key, True, time=BLACK_LIST_TIME)
        return {"message": "Email has been blacklisted"}

    except Exception as e:
        print(f"Error blacklisting email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to blacklist email")
