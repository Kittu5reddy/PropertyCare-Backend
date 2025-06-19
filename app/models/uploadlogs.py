from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.models import Base

class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String, nullable=False)  # e.g., "profile_photo", "pan", "aadhaar"
    file_path = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
