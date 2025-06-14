from pydantic import BaseModel,EmailStr
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_verified: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    token: str