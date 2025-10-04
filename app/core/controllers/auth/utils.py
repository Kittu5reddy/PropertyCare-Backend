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
from app.user.models.users import User
from app.user.models.personal_details import PersonalDetails
from app.core.models.property_details import PropertyDetails
from fastapi import status
# =================
#   settingsuration
# =================

ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY
# SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =================
#   Token Generator
# =================

def create_access_token(payload: dict, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, ACCES_TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(payload: dict, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload.update({"exp": expire})
    return jwt.encode(payload, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)




def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        is_pdfilled = payload.get("is_pdfilled")  
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user not found"
            )
        return {"sub": email,"is_pdfilled":is_pdfilled}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )



# ======================
#   Password Functions
# ======================

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ======================
#   User Validations
# ======================
def generate_user_id(id):
    return f'PC{datetime.utcnow().year}U{str(id).zfill(3)}'
def generate_employee_id(id):
    return f'PC{datetime.utcnow().year}E{str(id).zfill(3)}'
def generate_employee_superviser_id(id):
    return f'PC{datetime.utcnow().year}S{str(id).zfill(3)}'
def generate_employee_admin_id(id):
    return f'PC{datetime.utcnow().year}A{str(id).zfill(3)}'


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result:
        return result.scalar_one_or_none()
    else:
        raise HTTPException(401,details="unauthorized")

async def get_user_by_verification_token(db: AsyncSession, token: str) -> User:
    result = await db.execute(select(User).where(User.verification_token == token))
    return result.scalar_one_or_none()









from jose import jwt, JWTError, ExpiredSignatureError

async def get_current_user(token: str, db: AsyncSession) -> User:
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

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user






async def get_current_user_personal_details(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, ACCES_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result_user = await db.execute(select(User).where(User.email == email))
    user = result_user.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result_data = await db.execute(
        select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
    )
    data = result_data.scalar_one_or_none()

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal details not found",
        )

    return data

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import redis.exceptions
from jose import JWTError

def handle_exception(e: Exception, db=None):
    """
    Centralized exception handler for database, cache, JWT, and validation errors.
    Can be reused in any route.
    """
    # Rollback transaction if DB session is passed
    if db is not None:
        try:
            db.rollback()
        except Exception:
            pass

    if isinstance(e, HTTPException):
        raise e

    elif isinstance(e, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    elif isinstance(e, SQLAlchemyError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )

    elif isinstance(e, redis.exceptions.RedisError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache server error"
        )

    elif isinstance(e, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    elif isinstance(e, KeyError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required field: {e.args[0]}"
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


def get_is_pd_filled(token:str):
    payload=jwt.decode(token,ACCES_TOKEN_SECRET_KEY,algorithms=[ALGORITHM])
    # print(payload)
    return payload['is_pdfilled']

# =================
#   Example usage
# =================

if __name__ == "__main__":
    print(get_password_hash("Palvai2004@"))
