from pydantic import BaseModel, Field
from typing import List, Optional, Dict,Union
from datetime import datetime


# ---------- Services Schemas ----------
class ServiceBase(BaseModel):
    service_name: str
    category: str
    services: Optional[List[str]] = None
    is_active: Optional[bool] = False
    approx_cost_usd: int
    approx_cost_inr: int
    durations: List[str]
    applicable_to: Optional[Dict[str, List[Union[str, int]]]] = None  
    comments: Optional[str] = None
# Create Schema
class ServiceCreate(ServiceBase):
    pass
