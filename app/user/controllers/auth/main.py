from app.user.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash,verify_refresh_token,get_current_user,get_current_user_personal_details,verify_password,get_is_pd_filled
from app.user.controllers.auth.email import create_verification_token,send_verification_email
from fastapi import APIRouter,Request
from app.user.controllers.auth.utils import get_user_by_email,REFRESH_TOKEN_EXPIRE_DAYS,generate_user_id
from app.user.validators.auth import User as LoginSchema 
from app.user.models.users import User,UserNameUpdate
from app.user.models.personal_details import PersonalDetails
from fastapi import APIRouter, HTTPException,Depends,BackgroundTasks
from app.user.controllers.forms.utils import create_user_directory
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from fastapi.responses import HTMLResponse
from fastapi import Response
from passlib.context import CryptContext
from app.user.models import get_db,AsyncSession
from fastapi import Depends
from sqlalchemy import select, desc
from fastapi import BackgroundTasks
from app.user.validators.auth import ChangePassword
from app.user.validators.user_profile import ChangeFirstName,ChangeLastName,ChangeUsername,ChangeContactNumber,ChangeHouseNumber,ChangeStreet,ChangeCity,ChangeState,ChangeCountry,ChangePinCode
from app.user.controllers.forms.utils import get_image
from datetime import datetime,timedelta
auth=APIRouter(prefix='/auth',tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from fastapi.responses import JSONResponse







#=====================================================================================
#           LOGIN
#=====================================================================================



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
    payload = {"sub": user.email,"is_pdfilled":db_user.is_pdfilled}
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



#==========================================================================================
#           SIGNUP
#==========================================================================================

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



#=================================================================================================
#           EMAIL-VERFICIATION
#=================================================================================================


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


#=============================================================================================
#           REFRESH ROUTE
#============================================================================================


@auth.post("/refresh")
async def refresh_token(request: Request, response: Response,db:AsyncSession=Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        print("Missing refresh token")
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload =verify_refresh_token(refresh_token)
        access_token = create_access_token(payload)

        return {
            "access_token": access_token,
            "type": "Bearer"
        }
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")






#=============================
#   USER-REGISTRATION ROUTE
#=============================


@auth.get('/user-registration-status')
async def user_registration_status(
    token: str = Depends(oauth2_scheme)
):
    try:
        message= {"is_pdfilled":get_is_pd_filled(token)}
        return message
    except Exception as e:# Optional: log it
        raise HTTPException(status_code=401, detail="Invalid or expired token")


#=============================
#           CHANGE PASSWORD
#=============================


@auth.put("/change-password")
async def change_password(
    payload: ChangePassword,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: User = await get_current_user(token, db)

        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(status_code=403, detail="Wrong  password")

        user.hashed_password = get_password_hash(payload.new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "Password changed successfully"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
 









#===========================
#       PERSONAL DETAILS ROUTE
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

        
        profile_url=get_image(f"/user/{user.user_id}/profile_photo/profile_photo.png")
        return {
            "full_name": f"{data.first_name} {data.last_name}",
            "user_name": data.user_name,
            "contact_number": data.contact_number,
            "location": f"{data.city}, {data.state}",
            "member_from": data.created_at,
            "total_properties":200,
            "with_plans":20,
            "no_plans":180,
            "profile_photo_url":profile_url
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


#=============================
#    SUBSCRIPTION DETAILS
#=============================

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









#=========================================================================
#      Profie Edits
#=========================================================================

@auth.get("/edit-profile")
async def get_edit_profile_details(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(token, db)

        # Fetch personal details
        result = await db.execute(
            select(PersonalDetails).where(PersonalDetails.user_id == user.user_id)
        )
        data = result.scalar_one_or_none()

        if not data:
            raise HTTPException(status_code=404, detail="Personal details not found")

        # Fetch username update record
        result = await db.execute(
            select(UserNameUpdate).where(UserNameUpdate.user_id == user.user_id).limit(1)
        )
        username_update = result.scalar_one_or_none()

        # Determine if username is changable
        is_username_changable = False
        if username_update:
            last_updated = username_update.last_updated
            now = datetime.utcnow()
            delta = now - last_updated
            if delta > timedelta(days=30):  # e.g., allow username change after 30 days
                is_username_changable = True
        else:
            # No record means first time, so allow
            is_username_changable = True

        # Return profile data
        return {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "email": user.email,
            "user_name": data.user_name,
            "contact_number": data.contact_number,
            "house_number": data.house_number,
            "street": data.street,
            "city": data.city,
            "state": data.state,
            "pin_code": data.pin_code,
            "country": data.country,
            "image_url": get_image(f"/user/{user.user_id}/profile_photo/profile_photo.png"),
            "aadhaar_number": data.aadhaar_number,
            "pan_number": data.pan_number,
            "can_change_username": is_username_changable
        }
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")





@auth.put('/change-first-name')
async def change_first_name(
    form: ChangeFirstName,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.first_name = form.first_name.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "First name updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update first name: {str(e)}")


@auth.put('/change-last-name')
async def change_last_name(
    form: ChangeLastName,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.last_name = form.last_name.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "Last name updated successfully."}

    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update last name: {str(e)}")



# @auth.put('/change-username')
# async def change_username(
#     form: ChangeUsername,
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         user: PersonalDetails = await get_current_user_personal_details(token, db)
#         update_data:UserNameUpdate= await db.execute(select(UserNameUpdate).where(UserNameUpdate.user_id==user.user_id).limit((1)))
#         data=update_data.last_updated.scalar_or_none






@auth.put('/change-contact-number')
async def change_contact_number(
    form: ChangeContactNumber,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        result=await db.execute(select(PersonalDetails).where(PersonalDetails.contact_number!=form.contact_number).limit((1)))
        result=result.scalar_one_or_none()
        if result:
            return HTTPException(500,detail=f"number already exits")        
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.contact_number = form.contact_number.strip()
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "contact number updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update contact number: {str(e)}")







@auth.put('/change-house-number')
async def change_house_number(
    form: ChangeHouseNumber,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.house_number = form.house_number.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "house number updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update house number: {str(e)}")




@auth.put('/change-street')
async def change_street(
    form: ChangeStreet,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.street = form.street.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "street name updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update street name: {str(e)}")
    

@auth.put('/change-city')
async def change_city(
    form: ChangeCity,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.city = form.city.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "city  updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update city : {str(e)}")
    

    
@auth.put('/change-state')
async def change_state(
    form: ChangeState,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.state = form.state.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "state  updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update state name: {str(e)}")

@auth.put('/change-pin-code')
async def change_pin_code(
    form: ChangePinCode,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.pin_code = form.pin_code.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"message": "pin code updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update pin code: {str(e)}")
    

@auth.put('/change-country')
async def change_country(
    form: ChangeCountry,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        user: PersonalDetails = await get_current_user_personal_details(token, db)
        user.country = form.country.strip()

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"message": "country  updated successfully."}
    except HTTPException as http_exc:
        raise http_exc  # re-raise the actual HTTP error (like 401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update country : {str(e)}")

# /auth/change-username


#=============================
#           LOGOUT
#=============================

@auth.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")  # or whatever your cookie name is
    return {"message": "Logged out"}
