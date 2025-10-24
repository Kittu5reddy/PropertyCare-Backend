from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import Base


from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base


class RequiredAction(Base):
    __tablename__ = "required_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Link to user table
    user_id: Mapped[str] = mapped_column(
        String(50), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )

    # Use `for_type` or `action_for` instead of `FOR`
    action_for: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Indicates what the action is for: 'user', 'subscription', or 'document'."
    )

    # Flexible JSON field to support multiple use-cases
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    """
    Example structures:
    -------------------
    data = {"document_name": "EC", "property_id": "P001", "location": "Hyderabad"}
    data = {"end_date": "2025-12-31", "type": "premium", "property_id": "P002"}
    data = {"document_name": "Sale Deed", "expiry_date": "2026-01-01"}
    """

    status: Mapped[str] = mapped_column(String(50), default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
