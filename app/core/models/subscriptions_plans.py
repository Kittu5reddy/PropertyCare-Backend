from app.core.models import Base
from sqlalchemy import (
    JSON, Integer, String, Boolean, DateTime, func, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


class SubscriptionPlans(Base):
    __tablename__ = "subscriptions_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sub_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sub_type: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    services: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    cost: Mapped[int] = mapped_column(JSON, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )



class SubscriptionPlansHistory(Base):
    __tablename__ = "subscriptions_plans_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign key link to SubscriptionPlans
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions_plans.id", ondelete="CASCADE"), nullable=False
    )

    sub_id: Mapped[str] = mapped_column(String,index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sub_type: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    services: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    cost: Mapped[int] = mapped_column(JSON, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)

    # ✅ Action tracking fields
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE / UPDATE / DELETE
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    changed_by: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=True)

