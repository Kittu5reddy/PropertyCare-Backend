from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.models import Base
from sqlalchemy import Boolean,  DateTime, ForeignKey, Integer, String, func

class PropertyDocuments(Base):
    __tablename__ = "property_documents"   
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[str] = mapped_column(
        String(50), 
        ForeignKey("property_details.property_id"), 
        nullable=False,
        unique=True   # one-to-one with property
    )
    # Match column names with S3 filenames
    property_photo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    property_photos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    encumbrance_certificate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # instead of ec
    patta_title_deed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mutation_order: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tax_receipt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    layout_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # add if exists in S3
    lrs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bank_noc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    agreement_of_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )



class PropertyDocumentTransaction(Base):
    __tablename__ = "property_document_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to property
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("property_details.property_id"), nullable=False
    )

    # Link to admin/user who performed the action
    updated_by: Mapped[str] = mapped_column(
        String(50), ForeignKey("admin.admin_id"), nullable=True
    )

    # Document type changed (photo, ec, patta, etc.)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Action taken (uploaded, updated, deleted, verified, etc.)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

