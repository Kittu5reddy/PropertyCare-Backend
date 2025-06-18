from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class PCUserBase(BaseModel):
    first_name: str
    last_name: str
    username: str
    gender: str
    dob: str
    contact_number: str
    house_number: str
    street: str
    city: str
    state: str
    pin_code: str
    country: str
    pan_number: str
    aadhaar_number: str
    description: Optional[str] = ""

class PCUserCreate(PCUserBase):
    profile_photo_path: str
    pan_document_path: str
    aadhaar_document_path: str

class PCUserResponse(PCUserBase):
    id: int
    profile_photo_path: str
    pan_document_path: str
    aadhaar_document_path: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UsernameCheckResponse(BaseModel):
    username: str
    is_available: bool
