"""
QSFI AI Engine - FastAPI backend entrypoint.

This service will eventually host the AI-powered quantum stability analysis
and qubit recommendation features described on the QSFI frontend. For now it
only exposes a health check; application structure (services/, models/,
utils/) is scaffolded and ready for that logic to be added.
"""

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    AnalyzeResponse,
    CompareLatestResponse,
    ErrorResponse,
    HistoryResponse,
    UploadResponse,
)
from services.analysis_service import analyze_uploaded_csv
from services.compare_service import get_latest_comparison
from services.history_service import list_analyses
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


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["analysis"],
    summary="Upload and analyze a CSV file",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "Invalid file (wrong extension, empty, too large, or unparseable as CSV), "
                "missing required columns (Qubit/T1/T2), or no valid rows remain after cleaning."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "Request is missing the required `file` upload field.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server failed to save the uploaded file, or an unexpected error occurred.",
        },
    },
)
async def analyze_csv(
    file: UploadFile = File(..., description="CSV file to upload and analyze (.csv only, max 10 MB)."),
) -> AnalyzeResponse:
    """
    Uploads a CSV - reusing the same validation and file-saving logic as
    `/upload` - then runs `services.analyzer` on it: validates required
    columns, removes duplicate rows, drops rows with missing values,
    computes QSFI per qubit plus summary statistics, and assigns each
    qubit a Stable/Degrading status.
    """
    try:
        return await analyze_uploaded_csv(file)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error while analyzing the upload: {exc}",
        ) from exc


@app.get(
    "/history",
    response_model=HistoryResponse,
    tags=["analysis"],
    summary="List all saved analyses",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server failed to read saved analyses.",
        },
    },
)
def get_history() -> HistoryResponse:
    """Lists every analysis saved under `processed/` (filename + timestamp), newest first."""
    try:
        analyses = list_analyses()
        return HistoryResponse(count=len(analyses), analyses=analyses)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error while reading analysis history: {exc}",
        ) from exc


@app.get(
    "/compare/latest",
    response_model=CompareLatestResponse,
    tags=["analysis"],
    summary="Compare the two most recent analyses",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Fewer than two analyses have been saved yet.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server failed to read or compare saved analyses.",
        },
    },
)
def compare_latest() -> CompareLatestResponse:
    """
    Compares the two most recently saved analyses (by their saved
    timestamp) qubit-by-qubit - reusing the saved `processed/` results
    rather than recomputing anything from the original CSVs - and reports
    QSFI improvements/degradations, the change in average QSFI, and any
    qubits that newly became Stable or Degrading.
    """
    try:
        return get_latest_comparison()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error while comparing analyses: {exc}",
        ) from exc
