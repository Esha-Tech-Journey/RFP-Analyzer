"""Service layer — orchestrates file parsing, job creation, and task dispatch."""

import uuid
from pathlib import Path

from app.constants import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MIN_EXTRACTED_TEXT_LENGTH,
)
from app.models.rfp_job import RFPJob
from app.parsers.parser_factory import ParserFactory
from app.repositories.rfp_job_repository import RFPJobRepository
from app.tasks.analysis_task import analyse_rfp


class RFPJobService:
    """Orchestrates the full RFP submission workflow.

    Routers depend on this service. The service depends on the repository
    and parser abstractions — never on concrete types directly.
    """

    def __init__(self, repository: RFPJobRepository) -> None:
        """Initialise with an injected async repository."""
        self._repository = repository

    async def submit_rfp_file(self, filename: str, file_bytes: bytes) -> RFPJob:
        """Validate, parse, persist, and queue analysis for an uploaded RFP file.

        Args:
            filename:   Original filename from the multipart upload (e.g. "acme_rfp.pdf").
            file_bytes: Raw binary content of the uploaded file.

        Returns:
            The newly created RFPJob instance (status: pending).

        Raises:
            ValueError: On unsupported extension, file too large, or too little extracted text.
        """
        extension = self._extract_extension(filename)
        self._validate_extension(extension)
        self._validate_file_size(file_bytes)

        parser = ParserFactory.get_parser(extension)
        extracted_text = parser.extract_text(file_bytes)
        self._validate_extracted_text(extracted_text)

        title = self._derive_title(filename)
        rfp_job = await self._repository.create(title, filename, extension, extracted_text)

        analyse_rfp.delay(str(rfp_job.id))

        return rfp_job

    async def get_job(self, job_id: uuid.UUID) -> RFPJob | None:
        """Return a single RFPJob by ID, or None if not found.

        Args:
            job_id: UUID of the job to fetch.
        """
        return await self._repository.get_by_id(job_id)

    async def list_jobs(self) -> list[RFPJob]:
        """Return all RFPJob rows ordered by creation time (newest first)."""
        return await self._repository.list_all()

    async def submit_rfp_text(self, title: str, text: str) -> RFPJob:
        """Validate, persist, and queue analysis for manually entered RFP text.

        Args:
            title: Human-readable job title supplied by the user.
            text:  Full RFP content typed or pasted by the user.

        Returns:
            The newly created RFPJob instance (status: pending).

        Raises:
            ValueError: If the title is blank or the text is too short.
        """
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Title must not be blank.")

        self._validate_extracted_text(text)

        original_filename = f"{clean_title}.txt"
        rfp_job = await self._repository.create(
            clean_title, original_filename, "txt", text.strip()
        )

        analyse_rfp.delay(str(rfp_job.id))

        return rfp_job

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_extension(filename: str) -> str:
        """Return the lowercase file extension without the leading dot."""
        return Path(filename).suffix.lstrip(".").lower()

    @staticmethod
    def _validate_extension(extension: str) -> None:
        """Raise ValueError if the extension is not in ALLOWED_EXTENSIONS."""
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: .{extension}")

    @staticmethod
    def _validate_file_size(file_bytes: bytes) -> None:
        """Raise ValueError if the file exceeds the maximum allowed size."""
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError("File exceeds maximum size of 10 MB.")

    @staticmethod
    def _validate_extracted_text(text: str) -> None:
        """Raise ValueError if the extracted text is too short to be meaningful."""
        if len(text.strip()) < MIN_EXTRACTED_TEXT_LENGTH:
            raise ValueError("Could not extract meaningful text from the file.")

    @staticmethod
    def _derive_title(filename: str) -> str:
        """Derive a human-readable title from the filename stem."""
        stem = Path(filename).stem
        return stem.replace("_", " ").replace("-", " ").title()
