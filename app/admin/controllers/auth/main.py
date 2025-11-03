from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, Body,Request
from fastapi.responses import JSONResponse
from app.admin.models.admins import Admin
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import pwd_context
from app.admin.validators.admins import AdminLogin
from .utils import create_access_token,create_refresh_token,REFRESH_TOKEN_EXPIRE_DAYS
from sqlalchemy import select
from app.core.controllers.auth.utils import create_access_token,create_refresh_token,ACCES_TOKEN_SECRET_KEY,ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS,REFRESH_TOKEN_SECRET_KEY

admin_auth = APIRouter(prefix="/admin-auth",tags=["admin-auth"])


# ----------------------
# ADMIN LOGIN - SEND OTP
# ----------------------

@admin_auth.post("/login")
async def admin_login(
    payload: AdminLogin,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1️⃣ Get admin by email
    query = await db.execute(select(Admin).where(Admin.email == payload.email))
    admin = query.scalar_one_or_none()

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    # 2️⃣ Verify password
    if not pwd_context.verify(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3️⃣ If MFA is enabled — send verification code
    # if admin.MFA:
    #     # Example MFA handling (optional)
    #     background_tasks.add_task(send_mfa_email, admin.email)
    #     return JSONResponse(
    #         content={"message": "MFA enabled. Verification code sent to email."},
    #         status_code=200
    #     )

    # 4️⃣ Generate tokens
    payload_data = {"sub": admin.email, "role": "admin", "admin_id": admin.admin_id}
    access_token = create_access_token(payload_data,ACCES_TOKEN_SECRET_KEY=ACCES_TOKEN_SECRET_KEY,expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(payload_data,REFRESH_TOKEN_SECRET_KEY=REFRESH_TOKEN_SECRET_KEY,REFRESH_TOKEN_EXPIRE_DAYS=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # 5️⃣ Send tokens via response + cookies
    response = JSONResponse(content={
        "message": "Admin login successful",
        "access_token": access_token,
        "token_type": "Bearer"
    })
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/admin-auth/refresh"
    )

    return response





# --------------------------------
# REFRESH ACCESS TOKEN ENDPOINT
# --------------------------------
