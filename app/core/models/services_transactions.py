from app.core.models import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class ServicesTransactions(Base):
    __tablename__ = "services_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[int] = mapped_column(String, ForeignKey("services.service_id"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)  
    amount_usd: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False,default="PENDING")  
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    comments: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



from app.core.models import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func

class ServicesTransactionsHistory(Base):
    __tablename__ = "services_transactions_history"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("services_transactions.transaction_id"), nullable=False)
    edited_by = Column(String(50), ForeignKey("admin.admin_id"), nullable=False)
    changes_made = Column(JSON, nullable=True)   # Store JSON diff/changes
    action = Column(String(50), nullable=False) # e.g., CREATED, UPDATED, DELETED
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
