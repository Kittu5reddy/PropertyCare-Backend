from app.core.services.db import Base, metadata

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime, func,JSON,ARRAY


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admin_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    pd_filled:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False)

    MFA: Mapped[bool] = mapped_column(Boolean, default=False)

    mfa_secret: Mapped[str] = mapped_column(String, nullable=True)
    mfa_backup_codes: Mapped[list] = mapped_column(JSON, nullable=True)

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
