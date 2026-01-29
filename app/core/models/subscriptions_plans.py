from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, ForeignKey, func, JSON, text
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import Base

class SubscriptionPlans(Base):
    __tablename__ = "subscriptions_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    sub_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    sub_type: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False) # flats building

    # ✅ JSON and ARRAY properly typed
    services: Mapped[list[str] ] = mapped_column(ARRAY(String), nullable=True)
    durations: Mapped[dict[str,str]] = mapped_column(JSON, nullable=False) #all are months
    # cost was removed — pricing is handled elsewhere or per-transaction
    rental_percentages:Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("admin.admin_id"),  # ✅ schema-safe FK
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )




from sqlalchemy import (
    Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, ARRAY
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime

class SubscriptionPlanHistory(Base):
    __tablename__ = "subscription_plan_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 🔗 Reference to main plan
    subscription_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions_plans.id"), nullable=False
    )

    sub_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    sub_type: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    services: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=True
    )

    durations: Mapped[dict[str, str]] = mapped_column(
        JSON, nullable=False
    )

    rental_percentages: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    comments: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 🧑‍💼 Admin who performed the action
    admin_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("admin.admin_id"),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )

    # 🔍 Audit info
    action: Mapped[str] = mapped_column(
        String(30), nullable=False
        # CREATED, UPDATED, ACTIVATED, DEACTIVATED
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

