from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, Numeric
from app.core.models import Base
from datetime import datetime



class TransactionSubOffline(Base):
    __tablename__ = "transaction_sub_offline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # Link to user and property
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("property_details.property_id"), nullable=False)

    # Subscription plan reference
    sub_id: Mapped[str] = mapped_column(String(50), ForeignKey("subscriptions_plans.sub_id"), nullable=False)
    duration:Mapped[str]=mapped_column(Integer,nullable=False)


    # Unique transaction reference (internal/external)

    #cost at that time
    cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Payment details
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # CASH, CHEQUE, UPI, etc.
    payment_transaction_number: Mapped[str] = mapped_column(String(100),unique=True, nullable=False)  # UPI ref, cheque no., etc.


    # Status tracking (PENDING → APPROVED/REJECTED)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

