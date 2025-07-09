
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String,ForeignKey,Integer,Column
from app.models import Base
from sqlalchemy import Column, Integer, String, DateTime, func

class PersonalDetails(Base):
    __tablename__ = "personal_details"
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"))
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50),nullable=False)
    last_name: Mapped[str] = mapped_column(String(50),nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20),nullable=False)
    gender: Mapped[str] = mapped_column(String(10),nullable=False)
    contact_number: Mapped[int] = mapped_column(Integer,nullable=False)
    house_number: Mapped[str] = mapped_column(String(20),nullable=False)
    street: Mapped[str] = mapped_column(String(100),nullable=False)
    city: Mapped[str] = mapped_column(String(50),nullable=False)
    state: Mapped[str] = mapped_column(String(50),nullable=False)
    country: Mapped[str] = mapped_column(String(50),nullable=False)
    pincode: Mapped[str] = mapped_column(Integer,nullable=False)
    pan_number: Mapped[int] = mapped_column(String(10),nullable=False)
    aadhaar_number: Mapped[int] = mapped_column(String(10),nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
