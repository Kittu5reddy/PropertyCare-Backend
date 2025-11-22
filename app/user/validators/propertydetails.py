from pydantic import BaseModel
from typing import Optional,Annotated
from fastapi import Form

class PropertyDetailForm(BaseModel):

    property_name: str

    survey_number: Optional[str] = None
    plot_number: str


    house_number: str

    project_name_or_venture: Optional[str] = None
    street: str
    city: str
    state: str
    district: str
    mandal: str

    country: str = "India"
    pin_code: int

    size: float                        
    phone_number: str                  

    land_mark: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    gmap_url: Optional[str] = None
    facing: str
    type: str
    sub_type: str
    scale: str
    others: Optional[str] = None

    description: Optional[str] = None

    rental_income: Optional[float] = 0.0

    # foreign keys (frontend optional)
    admin_id: Optional[str] = None
    associates_id: Optional[str] = None


class UpdatePropertyNameRequest(BaseModel):
    property_name: str
