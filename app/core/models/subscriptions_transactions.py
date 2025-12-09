from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric, Boolean
from app.core.models import Base
from datetime import datetime


class SubscriptionsTransactions(Base):
    __tablename__ = "subscription_transactions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Internal transaction reference (tranXXXX)
    tran_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    property_id: Mapped[int | None] = mapped_column(ForeignKey("property_details.property_id"))
    sub_id: Mapped[int] = mapped_column(ForeignKey("subscriptions_plans.sub_id"), nullable=False)

    # Plan details
    starting_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ending_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # ---------- PayPhi Important Fields ----------
    merchant_id: Mapped[str] = mapped_column(String(20), nullable=False)
    merchant_txn_no: Mapped[str] = mapped_column(String(50), nullable=False)  # merchantTxnNo

    txn_id: Mapped[str | None] = mapped_column(String(30))   # PayPhi txnID
    payment_id: Mapped[str | None] = mapped_column(String(30))  # paymentID

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="356")

    payment_mode: Mapped[str | None] = mapped_column(String(20))        # CARD/UPI/NB
    payment_sub_inst_type: Mapped[str | None] = mapped_column(String(50))  # CC/DC/Bank Name

    response_code: Mapped[str | None] = mapped_column(String(10))
    response_description: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), default="INITIATED")
    payment_datetime: Mapped[datetime | None] = mapped_column(DateTime)

    # Optional fields
    hash_validated: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
