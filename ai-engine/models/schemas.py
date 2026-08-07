"""Pydantic request/response schemas shared across endpoints."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned after a CSV upload is validated, saved, and inspected."""

    success: bool = Field(..., description="Whether the upload completed successfully.")
    filename: str = Field(..., description="The unique filename the CSV was saved as under uploads/.")
    rows: int = Field(..., description="Number of data rows in the CSV, as read by pandas.")
    columns: list[str] = Field(..., description="Column headers found in the CSV.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "filename": "20260805_143022_a1b2c3d4_calibration.csv",
                "rows": 775,
                "columns": ["Qubit", "T1", "T2"],
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error body returned for 4xx/5xx responses."""

    detail: str
