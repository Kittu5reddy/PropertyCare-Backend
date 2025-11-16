from pydantic import BaseModel, Field
from typing import Optional

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    user_name: Optional[str] = Field(None)
    contact_number: Optional[str] = Field(None)
    house_number: Optional[str] = Field(None)
    street: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    pin_code: Optional[int] = Field(None)
    country: Optional[str] = Field(None)
