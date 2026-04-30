"""RFPDocumentContent SQLAlchemy ORM model — separated large text column."""

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RFPDocumentContent(Base):
    """Stores the extracted text separately from document metadata.

    Kept in its own table so that list queries on rfp_documents and rfp_jobs
    never load potentially large text blobs. Only joined when analysis needs it.
    """

    __tablename__ = "rfp_document_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rfp_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    document: Mapped["RFPDocument"] = relationship(
        "RFPDocument", back_populates="content"
    )
