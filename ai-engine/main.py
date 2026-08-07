"""
QSFI AI Engine - FastAPI backend entrypoint.

This service will eventually host the AI-powered quantum stability analysis
and qubit recommendation features described on the QSFI frontend. For now it
only exposes a health check; application structure (services/, models/,
utils/) is scaffolded and ready for that logic to be added.
"""

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import ErrorResponse, UploadResponse
from services.upload_service import save_and_inspect_csv
from utils.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for the Quantum State Fidelity Index (QSFI) platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Liveness check used by the frontend and deployment tooling."""
    return {"status": "running"}


@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["upload"],
    summary="Upload a CSV file",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid file (wrong extension, empty, too large, or unparseable as CSV).",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server failed to save the uploaded file.",
        },
    },
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload (.csv only, max 10 MB)."),
) -> UploadResponse:
    """
    Accepts a single CSV file, validates its type and size, saves it under
    `uploads/` with a unique timestamped filename, and reads it with pandas
    to report its row count and column names. No analysis is performed here.
    """
    try:
        return await save_and_inspect_csv(file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error while processing the upload: {exc}",
        ) from exc
