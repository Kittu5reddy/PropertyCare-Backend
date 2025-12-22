from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime



class AdditionalServiceCreate(BaseModel):
    service_id:str
    property_id:str
    category: str
    alternate_name:Optional[str]=None
    alternate_phone:Optional[str]=None


    
