"""Router for RFP job endpoints — /api/v1/jobs."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.rfp_job_repository import RFPJobRepository
from app.schemas.rfp_job import RFPJobDetailResponse, RFPJobResponse, RFPTextSubmitRequest
from app.services.rfp_job_service import RFPJobService

router = APIRouter(prefix="/api/v1/jobs", tags=["RFP Jobs"])


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------


def get_repository(db: AsyncSession = Depends(get_db)) -> RFPJobRepository:
    """Construct an RFPJobRepository bound to the current request's DB session."""
    return RFPJobRepository(db)


def get_service(
    repo: RFPJobRepository = Depends(get_repository),
) -> RFPJobService:
    """Construct an RFPJobService with an injected repository."""
    return RFPJobService(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=202, response_model=RFPJobResponse)
async def submit_rfp(
    file: UploadFile = File(...),
    service: RFPJobService = Depends(get_service),
) -> RFPJobResponse:
    """Accept a multipart file upload, parse it, and queue analysis.

    Returns 202 Accepted with the newly created job (status: pending).
    Returns 422 if the file type, size, or content is invalid.
    """
    file_bytes = await file.read()
    try:
        rfp_job = await service.submit_rfp_file(file.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RFPJobResponse.model_validate(rfp_job)


@router.post("/text", status_code=202, response_model=RFPJobResponse)
async def submit_rfp_text(
    body: RFPTextSubmitRequest,
    service: RFPJobService = Depends(get_service),
) -> RFPJobResponse:
    """Accept a plain-text RFP body and queue analysis.

    Returns 202 Accepted with the newly created job (status: pending).
    Returns 422 if the title is blank or the text is too short.
    """
    try:
        rfp_job = await service.submit_rfp_text(body.title, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RFPJobResponse.model_validate(rfp_job)


@router.get("", response_model=list[RFPJobResponse])
async def list_jobs(
    service: RFPJobService = Depends(get_service),
) -> list[RFPJobResponse]:
    """Return all submitted RFP jobs, newest first."""
    jobs = await service.list_jobs()
    return [RFPJobResponse.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=RFPJobDetailResponse)
async def get_job(
    job_id: uuid.UUID,
    service: RFPJobService = Depends(get_service),
) -> RFPJobDetailResponse:
    """Return the full detail of a single RFP job including analysis results.

    Returns 404 if no job with the given ID exists.
    """
    rfp_job = await service.get_job(job_id)
    if rfp_job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return RFPJobDetailResponse.model_validate(rfp_job)
