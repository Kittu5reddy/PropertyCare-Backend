
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String,ForeignKey,Integer,Column
from app.models import Base
from sqlalchemy import Column, Integer, String, DateTime, func,Text
from datetime import datetime
class PersonalDetails(Base):
    __tablename__ = "personal_details"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50),ForeignKey("users.user_id"), nullable=False, unique=True )
    user_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # fixed
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(10), nullable=False)  
    house_number: Mapped[str] = mapped_column(String(20), nullable=False)
    street: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    pin_code: Mapped[int] = mapped_column(Integer, nullable=False)  # fix: was String
    pan_number: Mapped[str] = mapped_column(String(10), nullable=False)  # fix: was int
    aadhaar_number: Mapped[str] = mapped_column(String(20), nullable=False)  # fix: was int
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
