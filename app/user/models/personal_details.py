
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String,ForeignKey,Integer,Column
from app.user.models import Base
from sqlalchemy import Column, Integer, String, DateTime, func,Text,Date
from datetime import datetime
class PersonalDetails(Base):
    __tablename__ = "personal_details"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50),ForeignKey("users.user_id"), nullable=False, unique=True )
    user_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # fixed
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[str] =  mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(10), nullable=False,unique=True)  
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




from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, JSON, Text
from datetime import datetime
from app.user.models import Base

class PersonalDetailsHistory(Base):
    __tablename__ = "personal_details_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to personal_details
    user_id: Mapped[str] = mapped_column(String(50),ForeignKey("users.user_id"), nullable=False )

    # Who updated the record (admin/user)
    updated_by_user: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=True)
    updated_by_admin: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=True)
    # Action performed
    action: Mapped[str] = mapped_column(String(50), nullable=False)  
    # e.g., "CREATE", "UPDATE", "DELETE"

    # Store old vs new values
    changes_made: Mapped[str] = mapped_column(String(50), nullable=False)

    remarks: Mapped[str] = mapped_column(Text, nullable=True)  # optional notes about the change

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
