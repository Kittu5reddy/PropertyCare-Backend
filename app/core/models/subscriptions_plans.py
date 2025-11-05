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
    category: Mapped[str] = mapped_column(String(255), nullable=False)

    # ✅ JSON and ARRAY properly typed
    services: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    cost: Mapped[dict] = mapped_column(JSON, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("PropCare.admin.admin_id"),  # ✅ schema-safe FK
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

    # ✅ Relationship to history
    history = relationship(
        "SubscriptionPlansHistory",
        back_populates="plan",
        cascade="all, delete-orphan"
    )


class SubscriptionPlansHistory(Base):
    __tablename__ = "subscriptions_plans_history"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # ✅ Foreign key to main plan table (schema-safe)
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscriptions_plans.id", ondelete="CASCADE"), nullable=False
    )

    sub_id: Mapped[str] = mapped_column(String(100), index=True)
    sub_type: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    services: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    cost: Mapped[dict] = mapped_column(JSON, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)

    # ✅ Audit fields
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE / UPDATE / DELETE
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    changed_by: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("admin.admin_id"),
        nullable=True
    )

    # ✅ Relationship back to main plan
    plan = relationship("SubscriptionPlans", back_populates="history")
