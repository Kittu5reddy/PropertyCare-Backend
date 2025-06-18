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
from config import Config
from app.models.users import User
from fastapi import status
# =================
#   Configuration
# =================

ACCES_TOKEN_SECRET_KEY = Config.ACCES_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = Config.REFRESH_TOKEN_SECRET_KEY
# SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = Config.REFRESH_TOKEN_EXPIRE_DAYS

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
        return payload
    except JWTError:
        raise HTTPException(401,detail="tamperd")

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
    return result.scalar_one_or_none()

async def get_user_by_verification_token(db: AsyncSession, token: str) -> User:
    result = await db.execute(select(User).where(User.verification_token == token))
    return result.scalar_one_or_none()










async def get_current_user(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, ACCES_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.user_name == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# =================
#   Example usage
# =================

if __name__ == "__main__":
    payload = {"sub": "kaushik"}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    print("Access Token:", access)
    print("Refresh Token:", refresh)