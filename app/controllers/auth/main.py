from app.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash,verify_refresh_token
from app.controllers.auth.email import create_verification_token,send_verification_email
from fastapi import APIRouter,Request
from app.controllers.auth.utils import get_user_by_email,REFRESH_TOKEN_EXPIRE_DAYS,generate_user_id
from app.validators.auth import User as LoginSchema 
from app.models.users import User
from fastapi import APIRouter, HTTPException,Depends,BackgroundTasks
from app.controllers.forms.utils import create_user_directory
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from fastapi.responses import HTMLResponse

auth=APIRouter(prefix='/auth',tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

from passlib.context import CryptContext
from app.models import get_db,AsyncSession
from fastapi import Depends
from sqlalchemy import select, desc

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.responses import JSONResponse

@auth.post("/login")
async def login(user: LoginSchema, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {"sub": user.email}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    response = JSONResponse(content={
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer"
    })

    # Set the refresh token as a secure HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,         # Use False if testing over HTTP
        samesite="strict",   # Or 'lax' or 'none' for cross-site
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,  # 7 days
        path="/auth/refresh"
    )
    return response


from fastapi import BackgroundTasks

@auth.post("/signup")
async def signup(
    user: LoginSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):

    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(user.password)
    token = create_verification_token()
    
    # Get the last user ID using async query
    result = await db.execute(select(User).order_by(desc(User.id)).limit(1))
    last_user = result.scalar_one_or_none()
    next_id = last_user.id + 1 if last_user else 1
    user_id = generate_user_id(next_id)
    
    new_user = User(
        user_id=user_id,
        email=user.email,
        hashed_password=hashed_password,
        verification_token=token,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    background_tasks.add_task(
        send_verification_email,
        new_user.email,
        new_user.verification_token
    )

    return {
        "message": "User created successfully. Please check your email to verify your account.",
        "email": new_user.email
    }


@auth.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str,
                        db: AsyncSession = Depends(get_db)):
    # Use async query to find user by verification token
    result = await db.execute(select(User).where(User.verification_token == token))
    user = result.scalar_one_or_none()
    
    if not user:
        return HTMLResponse(content="""
            <h2>Invalid or expired token</h2>
            <p>Please check your verification link or try signing up again.</p>
        """, status_code=400)
    if user.is_verified:
        return HTMLResponse(content="""
            <h2>Email already verified</h2>
            <p>You can now log in to your account.</p>
               
        """, status_code=200)
    user.is_verified = True
    user.verification_token = None  # Optional: Clear token after verification
    await db.commit()
    await create_user_directory(user.user_id)

    return HTMLResponse(content="""
        <h2>Email verification successful</h2>
        <p>Your email has been verified. You can now log in to your account.</p>
         <a href="http://localhost:5173/login">Click Here</a>
    """, status_code=200)


@auth.get("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        user=verify_refresh_token(refresh_token)
        encode=create_access_token(user)
        return {
            "access_token":encode,
            "type":"Bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

from fastapi import Response

@auth.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")  # or whatever your cookie name is
    return {"message": "Logged out"}
