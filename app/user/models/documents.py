from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.user.models import Base
class PropertyDocuments(Base):
    __tablename__ = "property_documents"   

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("property_details.property_id"), nullable=False
    )

    document_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 🔹 S3 storage reference
    s3_key: Mapped[str] = mapped_column(String(255), nullable=False)  

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserDocuments(Base):
    __tablename__ = "user_documents"   

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_id"), nullable=False
    )

    document_name: Mapped[str] = mapped_column(String(100), nullable=False)


    s3_key: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DocumentHistory(Base):
    __tablename__ = "document_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to property/user docs by document_id instead of generic documents
    document_id: Mapped[str] = mapped_column(String(50), nullable=False)

    updated_by: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.user_id"), nullable=False
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)  
    changes_made: Mapped[dict] = mapped_column(JSON, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
