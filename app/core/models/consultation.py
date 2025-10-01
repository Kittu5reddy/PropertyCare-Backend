from datetime import datetime, date, time
from sqlalchemy import String, Integer, DateTime, Date, Time, func, Text,Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base


class Consultation(Base):
    __tablename__ = "consultation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    preferred_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason_for_consultation: Mapped[str] = mapped_column(Text, nullable=True)
    complete:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


