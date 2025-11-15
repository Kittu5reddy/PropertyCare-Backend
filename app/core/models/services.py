from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

from app.core.models import Base


class Services(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    services: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)


    applicable_to: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True
    )

    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True   # 🔥 fix: allow null
    )

    short_comments: Mapped[Optional[str]] = mapped_column(
        String(110),
        nullable=True   # 🔥 fix: allow null
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class ServicesHistory(Base):
    __tablename__ = "services_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    service_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("services.service_id", ondelete="CASCADE"),
        nullable=False
    )

    edited_by: Mapped[str] = mapped_column(String(50), nullable=False)

    changes_made: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    action: Mapped[str] = mapped_column(String(50), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    updated_by: Mapped[str] = mapped_column(
        String,
        ForeignKey("admin.admin_id", ondelete="SET NULL"),
        nullable=False
    )
