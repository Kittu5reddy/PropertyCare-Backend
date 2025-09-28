from app.core.models import get_db,AsyncSession,redis_set_data,redis_get_data
from fastapi import Depends,APIRouter,HTTPException,Response
from fastapi.responses import JSONResponse
from app.admin.validators.admins import AdminLogin,OTP
from .utils import ADMIN_EMAILS,generate_otp,send_otp_email,create_access_token,create_refresh_token,REFRESH_TOKEN_EXPIRE_DAYS,verify_token,verify_refresh_token
from fastapi import BackgroundTasks
admin_auth=APIRouter(prefix="/admin-auth")



@admin_auth.post('/login')
async def admin_login(payload: AdminLogin, background_tasks: BackgroundTasks):
    email = payload.email
    if email in ADMIN_EMAILS:
        otp, expire = generate_otp(email)
        cache_key = f"admin:{email}:otp"
        await redis_set_data(cache_key, otp, time=expire)
        background_tasks.add_task(send_otp_email, email, otp)  # async send
        return {"message": "OTP sent to your email"}
    
    raise HTTPException(status_code=401, detail="Unauthorized admin")


@admin_auth.post('/verify-login')
async def admin_verify(payload: OTP,response:Response):
    try:
        otp = payload.otp
        email = payload.email
        cache_key = f"admin:{email}:otp"

        # Fetch OTP from Redis
        data = await redis_get_data(cache_key)
        if not data:
            raise HTTPException(status_code=404, detail="OTP not found or expired")
        if data != otp:
            raise HTTPException(status_code=401, detail="Invalid OTP")

        # Generate tokens
        access_token = create_access_token({"email": email})
        refresh_token= create_refresh_token( email=email)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=False,
            secure=True,
            samesite="None",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        # Return tokens in JSON response
        return {
            "login": "success",
            "access_token": access_token,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

from fastapi import Response, HTTPException, Body

@admin_auth.post("/admin-refresh")
async def admin_refresh_token(response: Response, refresh_token: str = Body(...)):
    """
    Refresh the access token using the JWT refresh token.
    The refresh token is set in an HTTP-only cookie.
    """
    email = verify_refresh_token(refresh_token)
    if not email or email not in ADMIN_EMAILS:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Generate new access token
    access_token = create_access_token({"email": email})

    # Return access token in JSON
    return {
        "access_token": access_token,
        "message": "Access token refreshed successfully"
    }
