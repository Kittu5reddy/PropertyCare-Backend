
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,ForeignKey
class Documents(Base):
    __tablename__ = "Documents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id:Mapped[str] = mapped_column(String(50))
    user_id: Mapped[str] = mapped_column(String(50),ForeignKey("user.id"))
    document_name:Mapped[str] = mapped_column(String(50))
    document_path:Mapped[str] = mapped_column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())