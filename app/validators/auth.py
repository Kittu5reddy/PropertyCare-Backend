from pydantic import BaseModel,EmailStr
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password: str



class EmailVerification(BaseModel):
    token: str



class ChangePassword(BaseModel):
    old_password:str
    new_password:str