

from app.core.controllers.auth.utils import (create_access_token,
                                             create_refresh_token,
                                             verify_refresh_token,
                                             verify_access_token

)

import secrets
# =========================
#    HELPER FUNCTIONS
# =========================
from fastapi import HTTPException
from pydantic import EmailStr
from jose import jwt,JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError,jwt
from config import settings
from app.user.models.users import User
from app.user.models.personal_details import PersonalDetails
from fastapi import status
from app.core.controllers.auth import ACCES_TOKEN_SECRET_KEY,ALGORITHM

async def get_user_by_email(db: AsyncSession, email: EmailStr) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result:
        return result.scalar_one_or_none()
    else:
        raise HTTPException(401,details="unauthorized")

async def get_user_by_verification_token(db: AsyncSession, token: str) -> User:
    result = await db.execute(select(User).where(User.verification_token == token))
    return result.scalar_one_or_none()

def create_verification_token():
    return secrets.token_urlsafe(32)




async def get_user_by_email(db: AsyncSession, email: EmailStr) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result:
        return result.scalar_one_or_none()
    else:
        raise HTTPException(401,details="unauthorized")



from jose import jwt, JWTError, ExpiredSignatureError

async def get_current_user(token: str, db: AsyncSession) -> User:
    try:
        print(token)
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
    print(email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        print(user)
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


def get_is_pd_filled(token:str):
    payload=jwt.decode(token,ACCES_TOKEN_SECRET_KEY,algorithms=[ALGORITHM])
    # print(payload)
    return payload['is_pdfilled']
