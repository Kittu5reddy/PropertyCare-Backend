from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, Boolean, Numeric, Enum,JSON
from app.user.models import Base
import enum
from datetime import datetime

# Enum for transaction status
class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class UserSubscriptionTransaction(Base):
    __tablename__ = "user_subscription_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)

    # Link to subscription
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Transaction details
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # external payment id
    amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., CARD, UPI, PAYPAL
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING)

    # Subscription duration details
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_by: Mapped[str] =mapped_column(String(50), ForeignKey("admin.admin_id"))




class UserSubscriptionTransactionHistory(Base):
    __tablename__ = "user_subscription_transaction_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to the original transaction
    transaction_ref_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_subscription_transactions.id"), nullable=False
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