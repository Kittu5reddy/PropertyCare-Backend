from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class SubscriptionPlanCreate(BaseModel):
    sub_type: str 
    category: str 
    services:  List[str]
    durations:dict[int, float]
    rental_percentages:Optional[dict[int,int]]=None
    comments: Optional[str] 
    is_active: Optional[bool] = Field(default=True)
