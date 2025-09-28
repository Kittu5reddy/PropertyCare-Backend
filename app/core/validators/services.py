from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ---------- Services Schemas ----------
class ServicesBase(BaseModel):
    service_id: str = Field(..., description="Unique service identifier")
    service_name: str = Field(..., max_length=50)
    services: Optional[List[str]] = None
    is_active: Optional[bool] = False
    approx_cost_usd: int
    approx_cost_inr: int
    durations: List[str]
    applicable_to: Optional[Dict] = None
    comments: Optional[str] = None
    created_by: str


class ServicesCreate(ServicesBase):
    """Validation schema for creating a new service"""
    pass


class ServicesUpdate(BaseModel):
    """Validation schema for updating a service (all optional)"""
    service_name: Optional[str] = None
    services: Optional[List[str]] = None
    is_active: Optional[bool] = None
    approx_cost_usd: Optional[int] = None
    approx_cost_inr: Optional[int] = None
    durations: Optional[List[str]] = None
    applicable_to: Optional[Dict] = None
    comments: Optional[str] = None


class ServicesOut(ServicesBase):
    """Read schema for returning a service"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   # works with SQLAlchemy ORM


# ---------- ServicesHistory Schemas ----------
class ServicesHistoryBase(BaseModel):
    service_id: str
    edited_by: str
    changes_made: Optional[Dict] = None
    action: str


class ServicesHistoryCreate(ServicesHistoryBase):
    """Validation schema for creating a history record"""
    pass


class ServicesHistoryOut(ServicesHistoryBase):
    """Read schema for returning a history record"""
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
