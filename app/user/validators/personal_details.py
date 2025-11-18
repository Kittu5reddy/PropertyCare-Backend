from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional

class Gender(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"


class PersonalDetails(BaseModel):
    first_name: str
    last_name: str
    user_name: str
    date_of_birth: date
    gender: str
    contact_number: str
    description: str
    house_number: str
    street: str
    city: str
    state: str
    country: str
    pin_code: int   
    nri: bool
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
