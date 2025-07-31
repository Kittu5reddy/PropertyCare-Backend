from app.user.models import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,ForeignKey


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    is_pdfilled = Column(Boolean, default=False)
    verification_token = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String,ForeignKey("admin.admin_id"))
    status = Column(String,default="active")
    
class UserNameUpdate(Base):
    __tablename__ = "user_name_updates"  # Important: Add a table name
    id = Column(Integer, primary_key=True, index=True)  # Needed for ORM mapping
    user_id = Column(String, index=True)  # Foreign key or link to User.user_id (if applicable)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())