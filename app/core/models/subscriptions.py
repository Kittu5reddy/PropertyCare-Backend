from app.core.models import Base
from sqlalchemy import  Integer, String, Boolean, DateTime, func,ForeignKey,Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column


class Subscriptions(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id:Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=False)
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
    payment_method: Mapped[str] = mapped_column(Text, nullable=True)
    comment:Mapped[str]=mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Reference to original subscription
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions.id"), nullable=False
    )

    admin_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("admin.admin_id"), nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_id"), nullable=False
    )

    sub_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("subscriptions_plans.sub_id"), nullable=False
    )

    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("property_details.property_id"), nullable=True
    )

    sub_name: Mapped[str] = mapped_column(String(20), nullable=False)

    services: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=True
    )

    sub_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    sub_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    durations: Mapped[int] = mapped_column(Integer, nullable=False)

    payment_method: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    comment: Mapped[str|None] = mapped_column(String(50), nullable=True)

    # 🔍 What happened
    action: Mapped[str] = mapped_column(
        String(30), nullable=False
        # examples: CREATED, UPDATED, RENEWED, CANCELLED, EXPIRED
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )