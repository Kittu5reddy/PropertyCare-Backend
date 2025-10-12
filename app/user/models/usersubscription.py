from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, Boolean, Numeric, Enum,JSON
from app.core.models import Base
import enum
from datetime import datetime
from typing import Optional
# Enum for transaction status

# -----------------------------
# User Subscription (who chose what plan)
# -----------------------------

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    
    # Link to subscription plan
    subscription_id: Mapped[int] = mapped_column(String, ForeignKey("subscriptions.sub_id"), nullable=False)

    # Subscription duration
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    amount_inr: Mapped[int] = mapped_column(Integer, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("admin.admin_id"))



class UserSubscriptionTransactionHistory(Base):
    __tablename__ = "user_subscription_transaction_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Link to the original transaction
    transaction_ref_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    # Who performed the change (admin/user)
    updated_by: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    # Action type
    action: Mapped[str] = mapped_column(String(50), nullable=False)  
    # e.g., "CREATE", "PAYMENT_SUCCESS", "PAYMENT_FAILED", "REFUND", "CANCELLED"
    # Store old vs new values
    changes_made: Mapped[dict] = mapped_column(JSON, nullable=True)
    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )