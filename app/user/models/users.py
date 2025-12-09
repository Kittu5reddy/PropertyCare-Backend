from app.core.models import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)

    # Universal user fields
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # NULL for OAuth users

    # OAuth fields
    oauth_provider = Column(String, nullable=True)        # google, meta, github, linkedin
    oauth_provider_id = Column(String, unique=True)       # Google sub / Facebook id
    oauth_avatar_url = Column(String, nullable=True)      # profile picture from provider

    # Optional provider token fields
    oauth_access_token = Column(String, nullable=True)
    oauth_refresh_token = Column(String, nullable=True)
    oauth_expires_at = Column(DateTime, nullable=True)

    # Verification fields
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)

    # User onboarding fields
    is_pdfilled = Column(Boolean, default=False)

    # Meta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Foreign key must reference the correct table name within the default schema.
    # The admins table is named 'admins' under the PropCare schema via Base metadata.
    created_by = Column(String, ForeignKey("admin.admin_id"), nullable=True)
    status = Column(String, default="active")

    
class UserNameUpdate(Base):
    __tablename__ = "user_name_updates"  # Important: Add a table name
    id = Column(Integer, primary_key=True, index=True)  # Needed for ORM mapping
    user_id = Column(String, index=True)  # Foreign key or link to User.user_id (if applicable)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())