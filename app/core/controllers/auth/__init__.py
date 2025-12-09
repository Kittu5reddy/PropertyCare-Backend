# =========================
#    HELPER FUNCTIONS
# =========================
from fastapi import HTTPException
from pydantic import EmailStr
from jose import jwt,JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError,jwt
from config import settings
# from app.user.models.users import User
# from app.user.models.personal_details import PersonalDetails
from fastapi import status
from datetime import datetime
# =================
#   settingsuration
# =================

ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY
# SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
FORGOT_PASSWORD_TIME_LIMIT=settings.FORGOT_PASSWORD_TIME_LIMIT
BASE_USER_URL=settings.BASE_USER_URL
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ======================
#   Password Functions
# ======================



# ======================
#   User Validations
# ======================





# =================
#   Example usage
# =================

# if __name__ == "__main__":
#     print(get_password_hash("Palvai2004@"))
