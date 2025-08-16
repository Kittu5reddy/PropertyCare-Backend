from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional

class PropertyDetailsBase(BaseModel):
    survery_number:str
    property_name: str
    plot_number: str
    house_number: str
    project_name_or_venture: Optional[str] = None
    street: str
    city: str
    state: str
    country: str = "India"
    pin_code: int
    size: int
    owner_name:str
    phone_number: str
    land_mark: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    facing: str
    type: str
    description: Optional[str] = None
