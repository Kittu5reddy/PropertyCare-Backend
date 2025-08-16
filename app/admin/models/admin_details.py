from app.user.models import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,ForeignKey,Text
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
class AdminDetails(Base):
    __tablename__ = "admin_details"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50),ForeignKey("admin.admin_id"), nullable=False, unique=True )
    user_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # fixed
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(10), nullable=False,unique=True)  
    house_number: Mapped[str] = mapped_column(String(20), nullable=False)
    street: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    pin_code: Mapped[int] = mapped_column(Integer, nullable=False)  
    pan_number: Mapped[str] = mapped_column(String(10), nullable=False)  
    aadhaar_number: Mapped[str] = mapped_column(String(20), nullable=False)  
    description: Mapped[str] = mapped_column(Text, nullable=True)
    role:Mapped[str] =  mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
