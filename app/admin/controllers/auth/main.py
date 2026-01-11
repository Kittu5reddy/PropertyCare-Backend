from fastapi import APIRouter,HTTPException,Depends,Response,Request
from app.admin.validators.auth.login import AdminLogin
from app.core.services.db import get_db,AsyncSession
from sqlalchemy import select
from app.admin.models.admin import Admin
from app.core.controllers.auth.utils import create_access_token,create_refresh_token,verify_password,verify_access_token,verify_refresh_token
from datetime import timedelta,datetime
from config import settings
admin_auth=APIRouter(prefix='/admin-auth',tags=['Admin Auth'])

from fastapi import Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

@admin_auth.post("/login")
async def admin_login(
    admin_data: AdminLogin,
    db: AsyncSession = Depends(get_db)
):
    # Fetch admin by email
    stmt = await db.execute(
        select(Admin).where(Admin.email == admin_data.email)
    )
    admin = stmt.scalar_one_or_none()

    if not admin or not verify_password(admin_data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Token payload
    payload = {
        "sub": admin.email,
        "role": "admin"
    }

    access_token = create_access_token(
        expires_delta=timedelta(minutes=5),
        payload=payload,
        secret_key=settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
    )

    refresh_token = create_refresh_token(
        expires_delta=timedelta(hours=6),
        payload=payload,
        secret_key=settings.REFRESH_TOKEN_SECRET_KEY_ADMIN
    )

    response = JSONResponse(
        content={
            "message": "Admin login successful",
            "access_token": access_token,
            "token_type": "Bearer"
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 6,
        path="/admin/auth/refresh"
    )

    return response



@admin_auth.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    payload = verify_refresh_token(refresh_token)
    access_token = create_access_token(
        expires_delta=timedelta(minutes=5),
        payload=payload,
        secret_key=settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
    )
    return {"access_token": access_token, "type": "Bearer"}




