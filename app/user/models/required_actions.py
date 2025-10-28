from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base


class RequiredAction(Base):
    __tablename__ = "required_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False
    )
    category: Mapped[str] = mapped_column(String, nullable=False)  
    information: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  
    status: Mapped[str] = mapped_column(String(10), default="pending")
    file_name: Mapped[str] = mapped_column(String, nullable=False)  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
