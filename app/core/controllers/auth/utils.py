from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.controllers.auth import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    ACCES_TOKEN_SECRET_KEY,
    pwd_context
)

# ====================================================
# JWT Token Creation (Access + Refresh)
# ====================================================

def create_access_token(
    payload: dict,
    expires_delta: timedelta | None = None,
    secret_key: str = ACCES_TOKEN_SECRET_KEY
) -> str:
    """
    Create a signed JWT access token.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = payload.copy()  # avoid modifying external dict
    payload.update({"exp": expire})

    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    payload: dict,
    expires_delta: timedelta | None = None,
    secret_key: str = REFRESH_TOKEN_SECRET_KEY
) -> str:
    """
    Create a signed JWT refresh token.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload = payload.copy()
    payload.update({"exp": expire})

    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


# ====================================================
# Token Verification (Access + Refresh)
# ====================================================

def verify_access_token(
    token: str,
    secret_key: str = ACCES_TOKEN_SECRET_KEY,
    algorithm: str = ALGORITHM
) -> dict:
    """
    Verifies JWT access token and returns payload.
    Handles:
      - Expired tokens
      - Invalid signatures
      - Malformed tokens
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> dict:
    """
    Verifies refresh token and extracts `sub` (email/user_id)
    + any extra claims like "is_pdfilled".
    """
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])

        email = payload.get("sub")
        is_pdfilled = payload.get("is_pdfilled")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in token",
            )

        return {"sub": email, "is_pdfilled": is_pdfilled}

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed refresh token",
        )

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "verify_refresh_token",
    "get_password_hash",
    "verify_password"
]
