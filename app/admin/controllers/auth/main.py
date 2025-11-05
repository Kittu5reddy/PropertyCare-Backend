from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, Body,Request,status
from fastapi.responses import JSONResponse
from app.admin.models.admins import Admin
from app.core.models import AsyncSession,get_db
from app.core.controllers.auth.main import pwd_context
from app.admin.validators.admins import AdminLogin
from datetime import datetime,timedelta
from sqlalchemy import select
from app.core.controllers.auth.utils import create_access_token,create_refresh_token
from .utils import verify_refresh_token_admin,ADMIN_ACCES_TOKEN_SECRET_KEY,ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES,ADMIN_REFRESH_TOKEN_EXPIRE_DAYS,ADMIN_REFRESH_TOKEN_SECRET_KEY
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
    query = await db.execute(select(Admin).where(Admin.email == payload.email))
    admin = query.scalar_one_or_none()

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if not pwd_context.verify(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload_data = {"sub": admin.email, "role": "admin", "admin_id": admin.admin_id}

    access_token = create_access_token(
        payload_data,
        ACCES_TOKEN_SECRET_KEY=ADMIN_ACCES_TOKEN_SECRET_KEY,
        expires_delta=timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_refresh_token(
        payload_data,
        REFRESH_TOKEN_SECRET_KEY=ADMIN_REFRESH_TOKEN_SECRET_KEY,
        expires_delta=timedelta(days=ADMIN_REFRESH_TOKEN_EXPIRE_DAYS)
    )

    response = JSONResponse({
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
        max_age=60 * 60 * 24 * ADMIN_REFRESH_TOKEN_EXPIRE_DAYS,
        path="/admin-auth/refresh"
    )

    return response


@admin_auth.post("/refresh")
async def admin_refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = verify_refresh_token_admin(refresh_token)

    new_access_token = create_access_token(
        payload,
        ACCES_TOKEN_SECRET_KEY=ADMIN_ACCES_TOKEN_SECRET_KEY,
        expires_delta=timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": new_access_token, "token_type": "Bearer"}

@admin_auth.post("/logout")
async def admin_logout(response: Response):
    """
    Securely log out the admin by clearing the refresh token cookie.
    """
    try:
        response = JSONResponse({"message": "Admin logged out successfully"})
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="none",
            path="/admin-auth/refresh"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")
