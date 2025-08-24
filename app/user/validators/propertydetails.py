from pydantic import BaseModel
from typing import Optional,Annotated
from fastapi import Form

class PropertyDetailForm(BaseModel):
    name: str
    project_name: str
    survey_number: str
    plot_number: str
    house_number: str
    street:str
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
    gmaps_url: Optional[str] = ""
    nearby_landmark: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    additional_notes: Optional[str] = ""

