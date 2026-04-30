"""Pydantic v2 request/response schemas for RFPJob API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants import MIN_EXTRACTED_TEXT_LENGTH


class RFPTextSubmitRequest(BaseModel):
    """Request body for the plain-text RFP submission endpoint."""

    title: str = Field(..., min_length=1, max_length=255, description="Human-readable job title.")
    text: str = Field(
        ...,
        min_length=MIN_EXTRACTED_TEXT_LENGTH,
        description="Full RFP content as plain text.",
    )


class RFPJobResponse(BaseModel):
    """Lightweight job representation returned by the list and submit endpoints."""

    id: UUID
    status: str
    created_at: datetime

    # Flattened from the document relationship
    title: str = ""
    original_filename: str = ""
    file_type: str = ""

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def flatten_document(self) -> "RFPJobResponse":
        """Pull document fields up to the top level if present."""
        # 'self' is the model instance; access the ORM object via __dict__ isn't needed
        # because from_attributes=True already resolved relationships.
        return self

    @classmethod
    def model_validate(cls, obj, **kwargs):  # type: ignore[override]
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "document") and obj.document is not None:
            instance.title = obj.document.title
            instance.original_filename = obj.document.original_filename
            instance.file_type = obj.document.file_type
        return instance


class RFPJobDetailResponse(RFPJobResponse):
    """Full job representation including analysis results."""

    error_message: str | None = None
    summary: list[str] | None = None
    requirements: list[str] | None = None
    risk_level: str | None = None
    risk_reasons: list[str] | None = None
    effort: str | None = None
    recommendation: str | None = None
    updated_at: datetime | None = None
    ai_summary: str | None = None
