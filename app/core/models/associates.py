from datetime import datetime, date, time
from sqlalchemy import String, Integer, DateTime, Date, Time, func, Text,JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base


class Associates(Base):
    __tablename__ = "associates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    associates_id :Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(10), nullable=True)

    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

