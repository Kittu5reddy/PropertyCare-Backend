from pydantic import BaseModel,EmailStr
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password: str



class EmailVerification(BaseModel):
    token: str



class ChangePassword:
    old_password:str
    new_password:str