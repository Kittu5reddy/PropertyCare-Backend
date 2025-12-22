from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    Text,
    func
)

from sqlalchemy.dialects.postgresql import (
    JSONB,
    ARRAY
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from datetime import datetime
from typing import Optional, List, Dict, Any

from app.core.models import Base  # adjust import as per your project



class AdditionalServiceTransaction(Base):
    __tablename__ = "additional_service_transactions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    transaction_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True
    )

    service_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("additional_services.service_id"),nullable=False
    )

    property_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("property_details.property_id"),nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        String(30), ForeignKey("users.user_id"),nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(10), nullable=False  # FLAT / PLOT
    )
    alternate_name:Mapped[str]=mapped_column(String,nullable=True)
    alternate_phone:Mapped[str]=mapped_column(String,nullable=True)
    service_status: Mapped[str] = mapped_column(
        String(20),
        default="REQUESTED"
        # REQUESTED | ASSIGNED | IN_PROGRESS | COMPLETED | CANCELLED
    )

    scheduled_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    completed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    amount: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    status:Mapped[Boolean]=mapped_column(String,default="PENDING")
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING"
        # PENDING | PAID | FAILED | REFUNDED
    )
    payment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class AdditionalServiceTransactionHistory(Base):
    __tablename__ = "additional_service_transaction_history"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    transaction_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey(
            "additional_service_transactions.transaction_id"
        ),

        index=True,
        nullable=False
    )

    history: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )
    """
    history = [
        {
            "service_status": "REQUESTED",
            "payment_status": "PENDING",
            "payment_type": null,
            "scheduled_date": "2025-01-15T10:00:00Z",
            "amount": 2500.00,
            "changed_by": "USR001",
            "change_reason": "Service requested",
            "changed_at": "2025-01-10T09:30:00Z"
        }
    ]
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
