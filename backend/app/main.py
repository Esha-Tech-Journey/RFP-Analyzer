"""FastAPI application factory with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import rfp_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    # Startup: nothing to initialise yet (DB engine added in Phase 2)
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="RFP Insight & Risk Analyzer",
        description="Evaluate incoming RFPs and generate structured risk analysis.",
        version="0.1.0",
        lifespan=lifespan,
        redirect_slashes=False,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Return a safe 500 response without leaking stack traces."""
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    @application.get("/health", tags=["Health"])
    async def health_check():
        """Return service health status."""
        return {"status": "ok"}

    application.include_router(rfp_jobs.router)

    return application


app = create_app()
