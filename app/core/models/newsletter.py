from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base
from config import settings


class NewsLetter(Base):
    __tablename__ = "news_letter"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # was just Column()
    status: Mapped[bool] = mapped_column(Boolean,default=True)  # was just Column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )







