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


class QubitResult(BaseModel):
    """A single qubit's computed QSFI and stability status."""

    qubit: int
    t1: float
    t2: float
    qsfi: float
    status: str


class BestWorstQubit(BaseModel):
    qubit: int
    qsfi: float


class AnalysisSummary(BaseModel):
    total_qubits: int
    average_t1: float
    average_t2: float
    average_qsfi: float
    best_qubit: BestWorstQubit
    worst_qubit: BestWorstQubit


class DataQuality(BaseModel):
    """Bookkeeping on how the raw upload was cleaned before analysis."""

    rows_received: int
    duplicate_rows_removed: int
    missing_values: dict[str, int]
    rows_with_missing_values_dropped: int
    rows_analyzed: int


class AnalyzeResponse(BaseModel):
    """Response returned by POST /analyze: services.analyzer's output plus upload/persistence metadata."""

    success: bool
    filename: str = Field(..., description="The unique filename the source CSV was saved as under uploads/.")
    processed_filename: str = Field(..., description="The filename this analysis was saved as under processed/.")
    analyzed_at: str = Field(..., description="UTC timestamp (ISO 8601) the analysis was run and saved.")
    summary: AnalysisSummary
    data_quality: DataQuality
    qubits: list[QubitResult]

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "filename": "20260805_143022_a1b2c3d4_quantum_data_day1.csv",
                "processed_filename": "20260805_143022_a1b2c3d4_quantum_data_day1.json",
                "analyzed_at": "2026-08-05T14:30:22.123456+00:00",
                "summary": {
                    "total_qubits": 155,
                    "average_t1": 0.00014699268600843761,
                    "average_t2": 0.00010441423661321995,
                    "average_qsfi": 0.00012570346131082877,
                    "best_qubit": {"qubit": 3, "qsfi": 0.0002338952681221},
                    "worst_qubit": {"qubit": 149, "qsfi": 3.519222175082278e-05},
                },
                "data_quality": {
                    "rows_received": 156,
                    "duplicate_rows_removed": 0,
                    "missing_values": {"Qubit": 0, "T1": 0, "T2": 1},
                    "rows_with_missing_values_dropped": 1,
                    "rows_analyzed": 155,
                },
                "qubits": [
                    {"qubit": 3, "t1": 0.00020176728056747127, "t2": 0.0002660232556767287, "qsfi": 0.0002338952681221, "status": "Stable"},
                ],
            }
        }
    }


class AnalysisHistoryEntry(BaseModel):
    """One saved analysis, as listed by GET /history."""

    filename: str = Field(..., description="Filename of the saved analysis under processed/.")
    analyzed_at: str = Field(..., description="UTC timestamp (ISO 8601) the analysis was run and saved.")


class HistoryResponse(BaseModel):
    """Response returned by GET /history."""

    count: int
    analyses: list[AnalysisHistoryEntry]

    model_config = {
        "json_schema_extra": {
            "example": {
                "count": 2,
                "analyses": [
                    {
                        "filename": "20260806_090000_bb11cc22_quantum_data_day2.json",
                        "analyzed_at": "2026-08-06T09:00:00.000000+00:00",
                    },
                    {
                        "filename": "20260805_143022_a1b2c3d4_quantum_data_day1.json",
                        "analyzed_at": "2026-08-05T14:30:22.123456+00:00",
                    },
                ],
            }
        }
    }


class AnalysisReference(BaseModel):
    """Points back to which uploaded file and timestamp a compared analysis came from."""

    filename: str | None
    analyzed_at: str | None


class QsfiChange(BaseModel):
    previous: float
    latest: float
    difference: float
    percent_change: float


class QubitQsfiChange(BaseModel):
    qubit: int
    previous_qsfi: float
    latest_qsfi: float
    difference: float


class QubitStatusChange(BaseModel):
    qubit: int
    previous_status: str
    latest_status: str


class CompareLatestResponse(BaseModel):
    """Response returned by GET /compare/latest."""

    previous: AnalysisReference
    latest: AnalysisReference
    qubits_compared: int = Field(..., description="Number of qubits present in both analyses and compared.")
    average_qsfi_change: QsfiChange
    improved_qubits: list[QubitQsfiChange]
    degraded_qubits: list[QubitQsfiChange]
    newly_stable_qubits: list[QubitStatusChange] = Field(
        ..., description="Qubits that were Degrading in the previous analysis and are Stable in the latest."
    )
    newly_unstable_qubits: list[QubitStatusChange] = Field(
        ..., description="Qubits that were Stable in the previous analysis and are Degrading in the latest."
    )
class TrendAnalysisReference(BaseModel):
    """Reference to the oldest or latest analysis used in trend analysis."""

    filename: str | None
    analyzed_at: str | None


class QubitHistoricalPoint(BaseModel):
    """
    One qubit's actual measured QSFI/T1/T2 from a single saved analysis.

    Sourced directly from that analysis's saved PostgreSQL record - never
    interpolated, estimated, or fabricated.
    """

    analysis_filename: str | None = Field(
        None, description="The unique filename this analysis was saved under in PostgreSQL."
    )
    filename: str | None = Field(
        None, description="The original uploaded CSV's filename (may repeat across analyses)."
    )
    analyzed_at: str | None = Field(
        None, description="UTC timestamp (ISO 8601) this analysis was run and saved."
    )
    qsfi: float
    t1: float
    t2: float


class QubitTrend(BaseModel):
    """Multi-day QSFI, T1, and T2 trend for one qubit."""

    qubit: int
    qsfi_day1: float
    qsfi_latest: float
    qsfi_change_percent: float
    qsfi_slope: float
    t1_slope: float
    t2_slope: float
    history: list[QubitHistoricalPoint] = Field(
        ...,
        description=(
            "This qubit's actual measured QSFI/T1/T2 from each saved analysis "
            "in the selected window, oldest first. Same length as "
            "days_analyzed for every qubit in `trends`, since a qubit missing "
            "from any selected analysis is excluded from `trends` entirely "
            "rather than given a fabricated point."
        ),
    )


class TrendResponse(BaseModel):
    """Response returned by GET /trend."""

    days_analyzed: int
    qubits_analyzed: int
    oldest: TrendAnalysisReference
    latest: TrendAnalysisReference
    trends: list[QubitTrend]


class RiskResult(BaseModel):
    """Prototype early-instability risk result for one qubit."""

    qubit: int
    risk_score: float
    risk_level: str
    qsfi_change_percent: float
    qsfi_slope: float
    t1_slope: float
    t2_slope: float


class RiskResponse(BaseModel):
    """Response returned by GET /risk."""

    days_analyzed: int
    qubits_analyzed: int
    oldest: TrendAnalysisReference
    latest: TrendAnalysisReference
    risk_results: list[RiskResult]
