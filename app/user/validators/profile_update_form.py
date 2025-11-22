from pydantic import BaseModel
from typing import Optional


class ProfileUpdateForm(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    house_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[int] = None
    country: Optional[str] = None
    isnri: Optional[bool] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None

    class Config:
        extra = "forbid"   # ❌ Reject unknown fields automatically
