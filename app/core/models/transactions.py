from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, ForeignKey, Boolean, Numeric, Enum,JSON
from app.core.models import Base
import enum
from datetime import datetime
from typing import Optional



# -----------------------------
# Transactions (payment details)
# -----------------------------

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Always link a transaction to a user subscription
    user_subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_subscriptions.id"), nullable=False)

    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # external payment id
    amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Payment info
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # ONLINE | OFFLINE
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)  # CARD, PAYPAL, CHEQUE, CASH, etc.

    # Extra reference fields (offline)
    offline_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cheque_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upi_ref_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    cash_receipt_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String, default="PENDING")

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
