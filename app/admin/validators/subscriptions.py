

from pydantic import BaseModel
from datetime import date
from typing import Optional

class AddSubscription(BaseModel):
    user_id: str
    property_id:str
    subscription_id: str
    start_date: date
    duration: int
    payment_method: str
    comment: str



class AddPlan(BaseModel):
    email:str
    phone:str