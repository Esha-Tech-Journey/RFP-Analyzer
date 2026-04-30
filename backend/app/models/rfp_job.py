"""RFPJob SQLAlchemy ORM model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus(str, enum.Enum):
    """Valid lifecycle states for an RFP analysis job."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RFPJob(Base):
    """One analysis run against an RFPDocument.

    Separated from the document so that:
    - risk_level, effort, recommendation are proper indexable columns
    - re-analysis of the same document is possible in the future
    - list queries never load extracted_text or large JSON blobs
    """

    __tablename__ = "rfp_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rfp_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jobstatus"), nullable=False, default=JobStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scalar analysis outputs — proper columns for filtering/sorting
    risk_level: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    effort: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    # Structured list outputs — kept as JSON (no query need)
    summary: Mapped[list | None] = mapped_column(JSON, nullable=True)
    requirements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # AI-generated full-text analysis from EPAM DIAL
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationship
    document: Mapped["RFPDocument"] = relationship("RFPDocument", back_populates="jobs")
