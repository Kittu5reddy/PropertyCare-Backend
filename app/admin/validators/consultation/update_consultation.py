from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time

class ConsultationUpdateItem(BaseModel):
    id: int

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_date: Optional[date] = None
    preferred_time: Optional[time] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        extra = "forbid"  # ❌ blocks created_at, id overwrite etc


from typing import List

class ConsultationUpdateRequest(BaseModel):
    updates: List[ConsultationUpdateItem]
