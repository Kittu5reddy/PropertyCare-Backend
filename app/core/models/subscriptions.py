from app.core.models import Base
from sqlalchemy import JSON, Column, Integer, String, Boolean, DateTime, func,ForeignKey,Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Subscriptions(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usub_id: Mapped[str] = mapped_column(String, unique=True,nullable=False, index=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    sub_id: Mapped[str] = mapped_column(String(50), ForeignKey("subscriptions_plans.sub_id"), nullable=False)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("property_details.property_id"), nullable=True)
    sub_name:Mapped[str]=mapped_column(String(20),nullable=False)
    # Subscription details
    services: Mapped[list[str] ] = mapped_column(ARRAY(String), nullable=True)
    sub_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sub_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    durations:Mapped[int]=mapped_column(Integer,nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    method:Mapped[str]=mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SubscriptionHistory(Base):
    __tablename__ = "subscriptions_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Snapshot fields
    usub_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_id: Mapped[str] = mapped_column(String(50), nullable=False)
    property_id: Mapped[str] = mapped_column(String(50), nullable=True)
    services: Mapped[list[str] ] = mapped_column(ARRAY(String), nullable=True)
    sub_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sub_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    durations:Mapped[int]=mapped_column(Integer,nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=True)

    # Audit fields
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE / UPDATE / CANCEL
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    changed_by: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=False)
