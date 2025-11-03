from pydantic import BaseModel

class AdminLogin(BaseModel):
    email:str
    password:str 

class OTP(BaseModel):
    email:str
    otp:str

class BlackListOTP(BaseModel):
    email:str