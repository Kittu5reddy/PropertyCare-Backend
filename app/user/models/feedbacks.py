from app.core.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, func, CheckConstraint,ForeignKey


class FeedBack(Base):
    __tablename__ = "feedbacks"  
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feedback_number = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(String,ForeignKey('users.user_id') ,index=True)   # FIXED
    property_id: Mapped[str] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('stars >= 0 AND stars <= 5', name='check_stars_range'),
    )
