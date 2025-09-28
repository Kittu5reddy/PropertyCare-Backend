from pydantic import BaseModel

class AdminLogin(BaseModel):
    email:str

class OTP(BaseModel):
    email:str
    otp:str