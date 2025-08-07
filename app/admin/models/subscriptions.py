from app.user.models import Base

from sqlalchemy import JSON, Column, Integer, String, Boolean, DateTime, func,ForeignKey


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    sub_id = Column(String, unique=True, index=True)
    created_by = Column(String(50), ForeignKey("admins.admin_id"), nullable=False)
    sub_type = Column(String(50), nullable=False)
    sub_name = Column(String(50), nullable=False)
    # Use SQLAlchemy's native JSON type for the property field
    services = Column(JSON, nullable=True)
    is_active= Column(Boolean,default=False)
    cost = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())




class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    created_by = Column(String(50), ForeignKey("admins.admin_id"), nullable=False)
    changes_made = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())