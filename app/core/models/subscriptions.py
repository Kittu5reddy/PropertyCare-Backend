from app.core.models import Base
from sqlalchemy import JSON, Column, Integer, String, Boolean, DateTime, func,ForeignKey,Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sub_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_by: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=False)

    sub_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_name: Mapped[str] = mapped_column(String(50), nullable=False)
    services: Mapped[dict] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_usd: Mapped[int] = mapped_column(Integer, nullable=False)  
    cost_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)  
    applicable_to: Mapped[dict] = mapped_column(JSON, nullable=True)
    comments:Mapped[str]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    edited_by = Column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    changes_made = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    action = Column(String(50), nullable=False)  # e.g., CREATED, UPDATED, DELETED
