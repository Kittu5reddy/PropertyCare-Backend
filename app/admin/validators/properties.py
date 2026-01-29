from pydantic import BaseModel



class UpdatePhysicalVerfication(BaseModel):
    property_id:str
    is_verified:bool




from pydantic import BaseModel
from typing import Optional,Annotated
from fastapi import Form

class AdminPropertyDetailForm(BaseModel):
    property_id: Optional[str] = None
    property_name: Optional[str] = None
    survey_number: Optional[str] = None
    plot_number: Optional[str] = None
    user_id: Optional[str] = None
    house_number: Optional[str] = None
    project_name_or_venture: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mandal: Optional[str] = None
    country: Optional[str] = "India"
    pin_code: Optional[int] = None
    size: Optional[float] = None
    phone_number: Optional[str] = None
    land_mark: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    gmap_url: Optional[str] = None
    facing: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    admin_id: Optional[str] = None
    description: Optional[str] = None
    scale:Optional[str] = None
    alternate_name:Optional[str] = None
    alternate_contact:Optional[str] = None


class UpdatePropertyNameRequest(BaseModel):
    property_name: str
