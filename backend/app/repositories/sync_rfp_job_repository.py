"""Synchronous repository used exclusively by the Celery worker."""

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.rfp_document_content import RFPDocumentContent
from app.models.rfp_job import JobStatus, RFPJob

_TERMINAL_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.completed, JobStatus.failed}
)


class SyncRFPJobRepository:
    """Synchronous persistence operations for the Celery worker."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, job_id: uuid.UUID) -> RFPJob | None:
        return self._session.get(RFPJob, job_id)

    def get_extracted_text(self, document_id: uuid.UUID) -> str | None:
        """Fetch extracted text for a document — only called by the worker."""
        row = self._session.execute(
            select(RFPDocumentContent).where(
                RFPDocumentContent.document_id == document_id
            )
        ).scalar_one_or_none()
        return row.extracted_text if row else None

    def update_status(self, job_id: uuid.UUID, status: JobStatus) -> None:
        job = self.get_by_id(job_id)
        if job is None or job.status in _TERMINAL_STATUSES:
            return
        self._session.execute(
            update(RFPJob).where(RFPJob.id == job_id).values(status=status)
        )
        self._session.commit()

    def save_results(self, job_id: uuid.UUID, results: dict[str, Any]) -> None:
        self._session.execute(
            update(RFPJob)
            .where(RFPJob.id == job_id)
            .values(
                summary=results.get("summary"),
                requirements=results.get("requirements"),
                risk_level=results.get("risk_level"),
                risk_reasons=results.get("risk_reasons"),
                effort=results.get("effort"),
                recommendation=results.get("recommendation"),
                ai_summary=results.get("ai_summary"),
                status=JobStatus.completed,
            )
        )
        self._session.commit()

    def save_error(self, job_id: uuid.UUID, message: str) -> None:
        """Record an error message and mark the job as failed."""
        self._session.execute(
            update(RFPJob)
            .where(RFPJob.id == job_id)
            .values(error_message=message, status=JobStatus.failed)
        )
        self._session.commit()
