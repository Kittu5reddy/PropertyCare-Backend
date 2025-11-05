from pydantic import BaseModel
from typing import Optional,Annotated
from fastapi import Form

class PropertyDetailForm(BaseModel):
    name: str
    survey_number:Optional[str]=""
    plot_number: str
    house_number: str
    city: str
    state: str
    district: str
    mandal: str
    pin_code: str
    size: str
    facing: str
    owner_name: str
    owner_contact: str
    type_of_property: str
    sub_type_property: str
    units:str
    country:Optional[str]="India"
    project_name: Optional[str] = ""
    street:Optional[str] = ""
    gmaps_url: Optional[str] = ""
    nearby_landmark: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    additional_notes: Optional[str] = ""
    associates_id:Optional[str] = ""
    rental_income:Optional[float] = 0.0

class UpdatePropertyNameRequest(BaseModel):
    property_name: str
