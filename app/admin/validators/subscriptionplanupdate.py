from pydantic import BaseModel
from typing import Optional, List

class SubscriptionPlanUpdate(BaseModel):
    sub_type: Optional[str] = None
    category: Optional[str] = None
    services: Optional[List[str]] = None
    durations: Optional[List[str]] = None
    comments: Optional[str] = None
    is_active: Optional[bool] = None
