"""Celery task for asynchronous RFP analysis.

IMPORTANT: This module must remain free of async/await, AsyncSession,
and asyncpg. It uses a synchronous SQLAlchemy session (psycopg2) only.
"""

import uuid
from dataclasses import asdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analysis.engine import AnalysisEngineFactory
from app.celery_app import celery_app
from app.config import settings
from app.models.rfp_job import JobStatus
from app.repositories.sync_rfp_job_repository import SyncRFPJobRepository

# Synchronous engine used only by this Celery worker module.
_sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
_SyncSession = sessionmaker(_sync_engine, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def analyse_rfp(self, job_id: str) -> None:
    """Fetch document content from DB, analyse it, and persist results."""
    parsed_job_id = uuid.UUID(job_id)

    with _SyncSession() as session:
        repository = SyncRFPJobRepository(session)
        try:
            job = repository.get_by_id(parsed_job_id)
            if job is None:
                return

            extracted_text = repository.get_extracted_text(job.document_id)
            if not extracted_text:
                repository.save_error(parsed_job_id, "Extracted text not found.")
                return

            repository.update_status(parsed_job_id, JobStatus.processing)

            analysis_result = AnalysisEngineFactory.create().analyse(
                str(job.document_id), extracted_text
            )

            repository.save_results(parsed_job_id, asdict(analysis_result))

        except Exception as exc:
            repository.save_error(parsed_job_id, str(exc))
            raise
