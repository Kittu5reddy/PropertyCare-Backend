# =========================
#    HELPER FUNCTIONS
# =========================
from fastapi import HTTPException
from pydantic import EmailStr
from jose import jwt,JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import Config
from app.models.setup import User

# =================
#   Configuration
# =================

ACCES_TOKEN_SECRET_KEY = Config.ACCES_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = Config.REFRESH_TOKEN_SECRET_KEY
# SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = Config.REFRESH_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =================
#   Token Generator
# =================

def create_access_token(payload: dict, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, ACCES_TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(payload: dict, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_MINUTES))
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
    return f'PC2025U{str(id).zfill(3)}'


def get_user_by_email(db: Session, email: EmailStr) -> User:
    return db.query(User).filter(User.email == email).first()

def get_user_by_verification_token(db: Session, token: str) -> User:
    return db.query(User).filter(User.verification_token == token).first()

# =================
#   Example usage
# =================

if __name__ == "__main__":
    payload = {"sub": "kaushik"}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    print("Access Token:", access)
    print("Refresh Token:", refresh)
