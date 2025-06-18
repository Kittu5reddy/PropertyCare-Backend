from app.models import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String)
