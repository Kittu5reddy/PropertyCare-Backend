from app.controllers.auth.utils import create_access_token,create_refresh_token,get_password_hash
from app.controllers.auth.email import create_verification_token,send_verification_email
from fastapi import APIRouter
from app.controllers.auth.utils import get_user_by_email
from app.validators.auth import User as LoginSchema 
from app.models.setup import User
from fastapi import APIRouter, HTTPException, status,Depends,BackgroundTasks
from app.models.setup import Session,get_db
auth=APIRouter(prefix='/auth',tags=['auth'])



@auth.post('/login')
def login(user: LoginSchema):
    if user.email == "kaushikpalvai2004@gmail.com" and user.password == "Palvai2004@":
        payload = {"sub": user.email}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

background_tasks=BackgroundTasks()
from fastapi import BackgroundTasks

@auth.post("/signup")
async def signup(
    user: LoginSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(user.password)
    token = create_verification_token()

    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        verification_token=token,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(
        send_verification_email,
        new_user.email,
        new_user.verification_token
    )

    return {
        "message": "User created successfully. Please check your email to verify your account.",
        "email": new_user.email
    }


from fastapi import Request
from fastapi.responses import HTMLResponse

@auth.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.verification_token == token).first()
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
    db.commit()

    return HTMLResponse(content="""
        <h2>Email verification successful</h2>
        <p>Your email has been verified. You can now log in to your account.</p>
    """, status_code=200)