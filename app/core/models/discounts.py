from sqlalchemy import Column, Integer, ARRAY,String, Float, Boolean, DateTime, ForeignKey

from datetime import datetime
from app.core.models import Base 

class Discounts(Base):
    __tablename__ = "discounts" 
    id = Column(Integer, primary_key=True)
    discount_id=Column(Integer, unique=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  
    description = Column(String(255), nullable=True)
    discount_type = Column(String(20), nullable=False, default="percentage")  
    value = Column(Float, nullable=False)  
    appliciable=Column(ARRAY(String), nullable=False) 
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    count=Column(Integer, nullable=True,default=-1)  
    

