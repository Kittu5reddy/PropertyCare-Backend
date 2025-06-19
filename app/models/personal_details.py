from app.models import Base
from sqlalchemy import  Column, Integer, String, Boolean, DateTime,Text,Date
from sqlalchemy import func


class PCUser(Base):
    __tablename__ = "personal_details_users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    user_name = Column(String(8), unique=True, index=True, nullable=False)
    gender = Column(String(10), nullable=False)
    dob = Column(Date, nullable=False)
    contact_number = Column(String(10), nullable=False, index=True)
    house_number = Column(String(50), nullable=False)
    street = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pin_code = Column(String(6), nullable=False)
    country = Column(String(100), nullable=False)
    pan_number = Column(String(10), nullable=False, index=True)
    aadhaar_number = Column(String(14), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


