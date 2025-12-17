import secrets

from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.controllers.auth.main import REFRESH_TOKEN_EXPIRE_DAYS
from config import settings
from app.core.services.db import  get_db
from app.core.services.redis import redis_client
from app.user.models.users import User
from app.core.controllers.auth.utils import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)


google_auth = APIRouter(prefix="/auth/google", tags=["auth-google"])
from .utils import *

@google_auth.get("/login")
async def google_login():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_OAUTH_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    state = secrets.token_urlsafe(16)
    await redis_client.setex(f"oauth:google:state:{state}", STATE_TTL, "1")
    return RedirectResponse(build_authorize_url(state))













@google_auth.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Validate state token
    key = f"oauth:google:state:{state}"
    saved = await redis_client.get(key)
    if not saved:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    await redis_client.delete(key)

    # Exchange code
    tokens = await exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access token from Google")

    # Fetch user info
    userinfo = await fetch_userinfo(access_token)
    email = userinfo.get("email")
    google_id = userinfo.get("sub")
    avatar = userinfo.get("picture")
    full_name = userinfo.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="Email scope not granted")

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # -----------------------------------------------------------
    #  NEW USER VIA GOOGLE LOGIN (Add random password here)
    # -----------------------------------------------------------
    if user is None:
        last = await db.execute(select(User).order_by(desc(User.id)).limit(1))
        last_user = last.scalar_one_or_none()
        next_id = (last_user.id + 1) if last_user else 1
        generated_user_id = generate_user_id(next_id)

        # Generate random password for your database
        random_password = secrets.token_urlsafe(16)
        hashed_pw = get_password_hash(random_password)

        user = User(
            user_id=generated_user_id,
            email=email,
            hashed_password=hashed_pw,     # 🔥 storing random password
            is_verified=True,
            oauth_provider="google",
            oauth_provider_id=google_id,
            oauth_avatar_url=avatar,
            status="active",
            is_pdfilled=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # OPTIONAL: send email to user with “You can login with OAuth or reset password”
        # send_password_info_email(email, random_password)

    # -----------------------------------------------------------
    #  EXISTING USER – Update OAuth info but DO NOT override their password
    # -----------------------------------------------------------
    else:
        updated = False

        if not user.is_verified:
            user.is_verified = True
            updated = True
        
        if not user.oauth_provider:
            user.oauth_provider = "google"
            updated = True

        if not user.oauth_provider_id:
            user.oauth_provider_id = google_id
            updated = True

        user.oauth_avatar_url = avatar
        updated = True
        
        if updated:
            db.add(user)
            await db.commit()
            await db.refresh(user)

    # Create tokens
    payload = {"sub": user.email, "is_pdfilled": user.is_pdfilled}
    app_access = create_access_token(payload)
    app_refresh = create_refresh_token(payload)

    FRONTEND_SUCCESS_URL = "https://user.vibhoospropcare.com/auth/success"
    
        # 2. Create the final URL with the access token as a query parameter
        # The frontend will read this token from the URL
    redirect_url = f"{FRONTEND_SUCCESS_URL}?access_token={app_access}&pd_filled={user.is_pdfilled}"

    # 3. Create a RedirectResponse object
    response = RedirectResponse(url=redirect_url, status_code=302)

    # 4. Set the refresh token cookie on the RedirectResponse object
    response.set_cookie(
        key="refresh_token",
        value=app_refresh,
        httponly=True,
        secure=True, # Should be True in production
        samesite="none", # Required for cross-site cookie
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth/refresh"
    )

    # 5. Return the response to the user's browser
    return response # <-- This is the redirect!