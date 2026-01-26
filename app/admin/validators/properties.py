from pydantic import BaseModel


class UpdatePhysicalVerfication(BaseModel):
    property_id:str
    is_verified:str