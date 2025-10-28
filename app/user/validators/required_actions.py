from pydantic import BaseModel
from typing import Optional


class RequiredActions(BaseModel):
    category: str
    file_name: str
    property_id: Optional[str] = None
