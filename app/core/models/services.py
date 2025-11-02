from app.core.models import Base
from sqlalchemy import JSON, Column, Integer, String, Boolean, DateTime, func,ForeignKey,Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime



class Services(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False) 
    services: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)
    durations: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    applicable_to: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ServicesHistory(Base):
    __tablename__ = "services_history"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, ForeignKey("services.service_id", ), nullable=False)
    edited_by = Column(String(50), nullable=False)  
    changes_made = Column(JSON, nullable=True)  # Store diff/changes as JSON
    action = Column(String(50), nullable=False)  # e.g., CREATED, UPDATED, DELETED
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
