from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, JSON,Boolean,Float,NUMERIC
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base
from config import settings


class PropertyDetails(Base):
    __tablename__ = "property_details"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # was just Column()
    property_name: Mapped[str] = mapped_column(String(50), nullable=False)
    survey_number: Mapped[str] = mapped_column(String(50), nullable=True)
    plot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    house_number: Mapped[str] = mapped_column(String(50), nullable=False)
    project_name_or_venture: Mapped[str] = mapped_column(String(100), nullable=True)
    street: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    district: Mapped[str] = mapped_column(String(50), nullable=False)
    mandal: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="India")
    pin_code: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[float] = mapped_column(Float, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(10), nullable=False)
    land_mark: Mapped[str] = mapped_column(Text, nullable=True)
    latitude: Mapped[str] = mapped_column(String(20), nullable=True)
    longitude: Mapped[str] = mapped_column(String(20), nullable=True)
    gmap_url: Mapped[str] = mapped_column(String(225), nullable=True)
    facing: Mapped[str] = mapped_column(String(20), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    others:Mapped[str]=mapped_column(String(100), nullable=True)
    sub_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scale:Mapped[str]=mapped_column(String(100), nullable=False)
    admin_id: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    description: Mapped[str] = mapped_column(Text, nullable=True)
    active_sub:Mapped[bool]=mapped_column(Boolean,default=False)
    rental_income:Mapped[float]=mapped_column(NUMERIC(10,2),nullable=True)
    associates_id:Mapped[str]=mapped_column(String(225),ForeignKey("associates.associates_id"),nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)




class PropertyHistory(Base):
    __tablename__ = "property_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # which property the history belongs to
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("property_details.id"), nullable=False)

    # who made the change
    updated_by_user: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=True)
    updated_by_admin: Mapped[str] = mapped_column(String(50), ForeignKey("admin.admin_id"), nullable=True)

    # type of action (CREATE / UPDATE / DELETE)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # store old/new values in JSON for audit
    changes_made: Mapped[dict] = mapped_column(JSON, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )




