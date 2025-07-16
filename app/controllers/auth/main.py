from app.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash,verify_refresh_token,get_current_user,verify_password
from app.controllers.auth.email import create_verification_token,send_verification_email
from fastapi import APIRouter,Request
from app.controllers.auth.utils import get_user_by_email,REFRESH_TOKEN_EXPIRE_DAYS,generate_user_id
from app.validators.auth import User as LoginSchema 
from app.models.users import User
from app.models.personal_details import PersonalDetails
from fastapi import APIRouter, HTTPException,Depends,BackgroundTasks
from app.controllers.forms.utils import create_user_directory
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from fastapi.responses import HTMLResponse
from fastapi import Response
from passlib.context import CryptContext
from app.models import get_db,AsyncSession
from fastapi import Depends
from sqlalchemy import select, desc
from fastapi import BackgroundTasks
from app.validators.auth import ChangePassword

auth=APIRouter(prefix='/auth',tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.responses import JSONResponse

@auth.post("/login")
async def login(
    user: LoginSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_email(db, user.email)

    # Check if user exists and password is correct
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # If user is not verified, resend verification email
    if not db_user.is_verified:
        # If token is None (maybe cleared previously), regenerate and update
        if not db_user.verification_token:
            db_user.verification_token = create_verification_token()
            await db.commit()
            await db.refresh(db_user)

        # Send email in background
        background_tasks.add_task(
            send_verification_email,
            db_user.email,
            db_user.verification_token
        )

        raise HTTPException(
            status_code=403,
            detail="Email not verified. A new verification email has been sent."
        )

    # Generate tokens
    payload = {"sub": user.email}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
 
    response = JSONResponse(content={
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer"
    })

    # Set refresh token as secure cookie
    response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,  # ✅ IMPORTANT: Required for samesite="none"
    samesite="none",  # ✅ Required for cross-origin
    max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
    path="/auth/refresh"
)

    return response



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
         <a href="https://propertycare-nine.vercel.app/login">Click Here</a>
    """, status_code=200)



@auth.post("/refresh")
async def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = verify_refresh_token(refresh_token)
        access_token = create_access_token(payload)
        
        # Also refresh the refresh token
        new_refresh_token = create_refresh_token(payload)
        
        # Set the new refresh token
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
            path="/auth/refresh"
        )
        
        return {
            "access_token": access_token,
            "type": "Bearer"
        }
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")







@auth.get('/user-registration-status')
async def user_registration_status(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: User = await get_current_user(token=token, db=db)
        return {"is_pdfilled": user.is_pdfilled}
    
    except Exception as e:# Optional: log it
        raise HTTPException(status_code=401, detail="Invalid or expired token")



@auth.put("/change-password")
async def change_password(
    payload: ChangePassword,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: User = await get_current_user(token, db)

        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Wrong current password")

        user.hashed_password = get_password_hash(payload.new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "Password changed successfully"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        # Log the error in production
        raise HTTPException(status_code=500, detail=str(e))










#===========================
# Profile
#===========================


@auth.get("/get-personal-data")
async def get_personal_details(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)

        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        data = result.scalar_one_or_none()

        if data is None:
            raise HTTPException(status_code=404, detail="Personal details not found")

        return {
            "full_name": f"{data.first_name} {data.last_name}",
            "user_name": data.user_name,
            "contact_number": data.contact_number,
            "location": f"{data.city}, {data.state}",
            "member_from": data.created_at,
            "total_properties":200,
            "with_plans":20,
            "no_plans":180
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@auth.get('/get-subscription-details')
async def get_subscription_details(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    try:
        user=await get_current_user(token,db)
        return [
        {
            "plan_type": "Basic",
            "property_covered": [
                {
                    "property_name": "Ramanthapur House",
                    "property_id": "1010101",
                    "location": "Hyderabad",
                    "property_type": "Residential"
                },
                {
                    "property_name": "Kukatpally Flat",
                    "property_id": "1010102",
                    "location": "Hyderabad",
                    "property_type": "Apartment"
                }
            ]
        },
        {
            "plan_type": "Premium",
            "property_covered": [
                {
                    "property_name": "Jubilee Hills Villa",
                    "property_id": "2020202",
                    "location": "Hyderabad",
                    "property_type": "Villa"
                },
                {
                    "property_name": "Madhapur Studio",
                    "property_id": "2020203",
                    "location": "Hyderabad",
                    "property_type": "Studio"
                }
            ]
        }
        ]
    except JWTError:
        raise HTTPException(401,detail="Unauthorized")



@auth.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")  # or whatever your cookie name is
    return {"message": "Logged out"}
