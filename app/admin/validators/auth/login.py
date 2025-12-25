from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time

class AdminLogin(BaseModel):
    email:str
    password:str
