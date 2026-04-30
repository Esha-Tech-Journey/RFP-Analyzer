"""Repository for all RFPJob and RFPDocument database operations."""

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rfp_document import RFPDocument
from app.models.rfp_document_content import RFPDocumentContent
from app.models.rfp_job import JobStatus, RFPJob

_TERMINAL_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.completed, JobStatus.failed}
)


class RFPJobRepository:
    """Encapsulates all persistence operations for RFPDocument and RFPJob entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        title: str,
        original_filename: str,
        file_type: str,
        extracted_text: str,
    ) -> RFPJob:
        """Insert a document + content + job row and return the persisted job."""
        document = RFPDocument(
            title=title,
            original_filename=original_filename,
            file_type=file_type,
        )
        self._session.add(document)
        await self._session.flush()  # get document.id

        content = RFPDocumentContent(
            document_id=document.id,
            extracted_text=extracted_text,
        )
        self._session.add(content)

        job = RFPJob(document_id=document.id)
        self._session.add(job)

        await self._session.commit()
        await self._session.refresh(job)
        await self._session.refresh(job, ["document"])
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> RFPJob | None:
        """Return the RFPJob with document eagerly loaded, or None."""
        result = await self._session.execute(
            select(RFPJob)
            .where(RFPJob.id == job_id)
            .options(selectinload(RFPJob.document))
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[RFPJob]:
        """Return all jobs with document eagerly loaded, newest first."""
        result = await self._session.execute(
            select(RFPJob)
            .options(selectinload(RFPJob.document))
            .order_by(RFPJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, job_id: uuid.UUID, status: JobStatus) -> None:
        """Update job status, guarding against overwriting terminal states."""
        job = await self.get_by_id(job_id)
        if job is None or job.status in _TERMINAL_STATUSES:
            return
        await self._session.execute(
            update(RFPJob).where(RFPJob.id == job_id).values(status=status)
        )
        await self._session.commit()

    async def save_results(self, job_id: uuid.UUID, results: dict[str, Any]) -> None:
        """Write analysis outputs and mark the job completed."""
        await self._session.execute(
            update(RFPJob)
            .where(RFPJob.id == job_id)
            .values(
                summary=results.get("summary"),
                requirements=results.get("requirements"),
                risk_level=results.get("risk_level"),
                risk_reasons=results.get("risk_reasons"),
                effort=results.get("effort"),
                recommendation=results.get("recommendation"),
                status=JobStatus.completed,
            )
        )
        await self._session.commit()

    async def save_error(self, job_id: uuid.UUID, message: str) -> None:
        """Record an error message and mark the job as failed."""
        await self._session.execute(
            update(RFPJob)
            .where(RFPJob.id == job_id)
            .values(error_message=message, status=JobStatus.failed)
        )
        await self._session.commit()

    async def get_content(self, document_id: uuid.UUID) -> RFPDocumentContent | None:
        """Return the extracted text content for a document."""
        result = await self._session.execute(
            select(RFPDocumentContent).where(
                RFPDocumentContent.document_id == document_id
            )
        )
        return result.scalar_one_or_none()
