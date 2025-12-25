from fastapi import APIRouter,HTTPException,Depends,Response
from app.core.services.db import get_db,AsyncSession
from sqlalchemy import select
from app.admin.models.admin import Admin
admin_mfa=APIRouter(prefix='/admin-mfa',tags=['Admin Auth'])
from app.core.controllers.auth.utils import create_access_token,create_refresh_token
from .utils import generate_mfa_qr,generate_backup_codes,verify_mfa_token
from config import settings
from datetime import datetime,timedelta
ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY_ADMIN
# SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN



@admin_mfa.post("/generate-mfa-qr")
async def generate_mfa_qr_route(
    email:str,
    db: AsyncSession = Depends(get_db)
):
    try:
 
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 2️⃣ Fetch admin
        result = await db.execute(
            select(Admin).where(Admin.email == email)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        if admin.MFA:
            raise HTTPException(
                status_code=400,
                detail="MFA already enabled"
            )

        # 3️⃣ Generate MFA QR + secret
        mfa_data = generate_mfa_qr(admin.email)

        # 4️⃣ Generate backup codes
        plain_codes, hashed_codes = generate_backup_codes()

        # 5️⃣ Save to DB (IMPORTANT)
        admin.mfa_secret = mfa_data["secret"]
        admin.mfa_backup_codes = hashed_codes
        admin.MFA = True  # still false until verified

        await db.commit()

        # 6️⃣ Return ONLY what frontend needs
        return {
            "qr_code": mfa_data["qr_code"],
            "backup_codes": plain_codes
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate MFA QR"
        )

@admin_mfa.post("/verify-mfa-token")
async def admin_verify_mfa_token(
    email:str,
    otp: str,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 🔐 Decode temp token

        admin_email=email

        if not admin_email:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(
            select(Admin).where(Admin.email == admin_email)
        )
        admin = result.scalar_one_or_none()

        if not admin or not admin.mfa_secret:
            raise HTTPException(status_code=400, detail="MFA not setup")

        # 🔢 Verify OTP
        if not verify_mfa_token(admin.mfa_secret, otp):
            raise HTTPException(status_code=401, detail="Invalid OTP")

        # ✅ Enable MFA
        admin.MFA = True
        await db.commit()

        # 🔑 Create tokens
        access_token = create_access_token(
            data={
                "sub": admin.email,
                "admin_id": admin.admin_id,
                "role": "admin",
                "mfa_verified": True
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            secret_key=ACCES_TOKEN_SECRET_KEY
        )

        refresh_token = create_refresh_token(
            data={
                "sub": admin.email,
                "admin_id": admin.admin_id,
                "role": "admin"
            },
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            secret_key=REFRESH_TOKEN_SECRET_KEY
        )

    
        response.set_cookie(
            key="admin_refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return {
            "access_token":access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="MFA verification failed")
