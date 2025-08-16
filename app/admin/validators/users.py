from pydantic import BaseModel,EmailStr
from datetime import datetime


class UserDynamicUpdate(BaseModel):
    updates: dict[str, str]

class ChangePassword(BaseModel):
    new_password:str
class ChangeEmail(BaseModel):
    new_email:str


