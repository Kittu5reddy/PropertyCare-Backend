from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.models import Base
from typing import Optional

class UserDocuments(Base):
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True   # one-to-one with user
    )

    # PAN and Aadhaar
    pan_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aadhar_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optional file references (S3 paths, if you store file links)
    pan_file: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    aadhar_file: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserDocumentHistory(Base):
    __tablename__ = "user_document_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to the user document
    user_document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_documents.id"), nullable=False
    )

    # Who updated it (user themselves)
    updated_by: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_id"), nullable=False
    )

    # Action type: UPLOAD / UPDATE / DELETE / VERIFY
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Old vs new values (optional)
    changes_made: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

