from pydantic import BaseModel,EmailStr
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email:str
    token: str
    new_password: str
