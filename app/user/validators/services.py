from pydantic import BaseModel
from typing import Optional

class AddService(BaseModel):
    alternate_name:Optional[str]=""
    alternate_phonenumber:Optional[str]=""
    service_id:str
    property_id:str