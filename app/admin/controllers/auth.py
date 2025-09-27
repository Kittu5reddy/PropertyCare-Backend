from fastapi import APIRouter,Depends,BackgroundTasks,HTTPException,Request,Response
from app.core.models import get_db,AsyncSession
from app.admin.models.admins import Admin
from app.user.validators.auth import User as UserSchema
from app.core.controllers.auth.main import oauth2_scheme
from app.core.controllers.auth.utils import create_access_token,create_refresh_token,verify_password,verify_refresh_token,get_password_hash
from sqlalchemy import select
from config import settings
from jose import jwt,JWTError
from fastapi import status
from app.core.controllers.auth.email import send_admin_login_alert_email
from fastapi.responses import HTMLResponse,JSONResponse
from app.core.controllers.auth.main import  pwd_context

ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN=settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN
REFRESH_TOKEN_EXPIRE_DAYS_ADMIN=settings.REFRESH_TOKEN_EXPIRE_DAYS_ADMIN
ACCES_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY
# SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM



admin=APIRouter(prefix='/admin',tags=['admin'])




@admin.get('/get-current-admin')
def get_current_admin(token:str=Depends(oauth2_scheme),db:AsyncSession=Depends(get_db)):
    try:
        payload = jwt.decode(token, ACCES_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        admin_id = payload.get("admin_id")
        if email is None:
            print("email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user not found"
            )
        return {"sub": email, "admin_id" :admin_id}
    except JWTError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

from fastapi import HTTPException, status

@admin.post('/login')
async def login(
    schema: UserSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Correctly await the DB call
        result = await db.execute(select(Admin).where(Admin.email == schema.email))
        admin: Admin = result.scalar_one_or_none()
        if not admin:
            raise HTTPException(status_code=401, detail="Email Does Not Exist")
        if not admin or not pwd_context.verify( schema.password,admin.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        # Add background email task with correct parameter order:
        background_tasks.add_task(
            send_admin_login_alert_email,
            admin.email,                                 # admin's email
            request.client.host,                         # IP address
            request.headers.get("user-agent")            # User-Agent string
        )

        # Generate tokens
        payload = {"sub": admin.email, "admin_id": admin.admin_id}
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
            secure=False,
            samesite="none",
            max_age=60 * 60 * 24 * 1,
            path="/admin/token/refresh"
        )
        return response
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))





@admin.post("/admin/token/refresh")
async def refresh_token(request: Request, response: Response,db:AsyncSession=Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        print("Missing refresh token")
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload =jwt.decode(refresh_token,REFRESH_TOKEN_SECRET_KEY,algorithms=[ALGORITHM])
        if not payload.get('sub',None):
            raise HTTPException(status_code=401, detail="Token Tampered")
        
        access_token = create_access_token(payload,ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN)

        return {
            "access_token": access_token,
            "type": "Bearer"
        }
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@admin.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")  # or whatever your cookie name is
    return {"message": "Logged out"}