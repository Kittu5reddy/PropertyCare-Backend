from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from fastapi import UploadFile
class PCFORM(BaseModel):
    first_name: str 
    last_name: str 
    user_name: str 
    gender: str
    dob: date  # Ensure the frontend sends date in "YYYY-MM-DD" format
    contact_number: str  # or int if strictly numeric
    house_number: str
    street: str
    city: str
    state: str
    pin_code: str
    country: str
    pan_number: str
    aadhaar_number: str

