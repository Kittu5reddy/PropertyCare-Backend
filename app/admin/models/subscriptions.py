from app.user.models import Base

from sqlalchemy import JSON, Column, Integer, String, Boolean, DateTime, func,ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    sub_id = Column(String, unique=True, index=True)
    created_by = Column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    sub_type = Column(String(50), nullable=False)
    sub_name = Column(String(50), nullable=False)
    services = Column(JSON, nullable=True)   # ok, but see note below
    is_active= Column(Boolean, default=False)
    cost_usd = Column(Integer, nullable=False)
    cost_inr = Column(Integer, nullable=False)

    durations = Column(ARRAY(String), nullable=False)   # ⚠️ works only with PostgreSQL
    applicable_to = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    created_by = Column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    changes_made = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    action = Column(String(50), nullable=False)  # e.g., CREATED, UPDATED, DELETED
