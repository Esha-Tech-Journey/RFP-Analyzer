"""RFPDocument SQLAlchemy ORM model — immutable document record."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RFPDocument(Base):
    """Immutable record of an uploaded RFP document.

    Separating document metadata from job results allows:
    - List queries that never touch large text
    - Future re-analysis without re-uploading
    """

    __tablename__ = "rfp_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped["RFPDocumentContent"] = relationship(
        "RFPDocumentContent", back_populates="document", uselist=False, lazy="select"
    )
    jobs: Mapped[list["RFPJob"]] = relationship(
        "RFPJob", back_populates="document", lazy="select"
    )
