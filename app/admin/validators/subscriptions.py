

from pydantic import BaseModel
from datetime import date
from typing import Optional

class AddSubscription(BaseModel):
    user_id: str
    property_id: Optional[str] = None
    sub_id: str
    start_of_sub: date
    duration: int
    payment_method: str
    comment: Optional[str] = None



