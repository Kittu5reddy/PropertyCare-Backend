from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class Consultation(BaseModel):
    name: str
    email: EmailStr
    phone: str 
    preferred_date: date
    preferred_time: time
    type:str
    comment:Optional[str]=None