from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class Consultation(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    preferred_date: date
    preferred_time: time
    reason_for_consultation: Optional[str] = None