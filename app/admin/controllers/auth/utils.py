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
ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY_ADMIN
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY_ADMIN
# SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN


async def get_current_admin(token:str=Depends(oauth2_scheme),
                            db:AsyncSession=Depends(get_db)):
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
            raise HTTPException(status_code=404, detail="User not found")

        return admin


