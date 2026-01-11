from app.core.services.db import get_db,AsyncSession
from app.admin.models.admin import Admin 
from jose import JWTError,jwt,ExpiredSignatureError
from fastapi import HTTPException,status
from sqlalchemy import select
from config import settings

ACCES_TOKEN_SECRET_KEY=settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
REFRESH_TOKEN_SECRET_KEY=settings.REFRESH_TOKEN_SECRET_KEY_ADMIN
ALGORITHM=settings.ALGORITHM


async def get_current_admin(token: str, db: AsyncSession) -> Admin:
    try:
        payload = jwt.decode(token, ACCES_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    result = await db.execute(select(Admin).where(Admin.email == email))
    admin = result.scalar_one_or_none()
    if admin is None:
        print(admin)
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin
