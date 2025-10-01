from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, JSON,Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base
from config import settings


class NewsLetter(Base):
    __tablename__ = "news_letter"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # was just Column()
    status: Mapped[str] = mapped_column(Boolean,default=True)  # was just Column()
    





