from app.core.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime, func


class Admin(Base):
    __tablename__ = "admin"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    MFA: Mapped[bool] = mapped_column(Boolean, default=False)  # Multi-Factor Auth flag
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
