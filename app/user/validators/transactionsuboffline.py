from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransactionSubOffline(BaseModel):
    property_id: str
    sub_id: str 
    category:str
    cost: float
    transaction_id: Optional[str] = None
    payment_method: str 
    payment_transaction_number: str
    status: Optional[str] = Field("PENDING")

