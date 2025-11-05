from app.core.controllers.auth.main import oauth2_scheme 
from app.core.models import AsyncSession,get_db
from fastapi import Depends,status,HTTPException
from config import settings
from jose import jwt,ExpiredSignatureError,JWTError
from sqlalchemy import select
from app.admin.models.admins import Admin
#==================
#    CONSTANTS
#==================
ADMIN_ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
ADMIN_REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY_ADMIN
# SECRET_KEY = settings.SECRET_KEY
ADMIN_ALGORITHM = settings.ALGORITHM
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN
ADMIN_REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN




async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    ✅ Validate JWT and confirm admin exists & is active.
    """
    try:
        payload = jwt.decode(token, ADMIN_ACCES_TOKEN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        admin_id: str = payload.get("admin_id")

        if not email or role != "admin":
            raise HTTPException(status_code=401, detail="Invalid token or role")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    result = await db.execute(select(Admin).where(Admin.email == email))
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if hasattr(admin, "is_active") and not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is deactivated")

    return admin


def verify_refresh_token_admin(token: str):
    try:
        payload = jwt.decode(token, ADMIN_REFRESH_TOKEN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")

        if not email or role != "admin":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
