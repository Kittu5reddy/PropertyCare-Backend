from typing import List, Dict, Optional
from pydantic import BaseModel

class SubscriptionPlan(BaseModel):
    sub_type: str
    category: str
    services: Optional[List[str]] = None
    durations: List[str]
    cost: Dict[int, int]  
    comments: Optional[str] = None
    created_by: str
    is_active: Optional[bool] = False
