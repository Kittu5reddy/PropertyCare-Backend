from sqlalchemy.orm import Mapped, mapped_column
from app.user.models import Base
from sqlalchemy import String, DateTime, func, ForeignKey, Integer,Text,JSON
from datetime import datetime
class Documents(Base):
    __tablename__ = "documents"   

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # link to user table
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)

    document_name: Mapped[str] = mapped_column(String(100), nullable=False)
    document_path: Mapped[str] = mapped_column(Text, nullable=False)  # longer path length

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())




class DocumentHistory(Base):
    __tablename__ = "document_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # which document the history belongs to
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)

    # who made the change
    updated_by: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)

    # type of action performed
    action: Mapped[str] = mapped_column(String(50), nullable=False)  
  

    # old vs new values
    changes_made: Mapped[dict] = mapped_column(JSON, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )