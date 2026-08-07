"""
QSFI analysis service.

Takes a pandas DataFrame of raw qubit readings (Qubit, T1, T2) and returns a
single JSON-ready dict of validated, cleaned, and computed results. This
module is intentionally framework-agnostic (no FastAPI/HTTP concerns) so it
can be unit-tested and reused independently of any endpoint - callers are
responsible for turning the ValueErrors raised here into HTTP responses.
"""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("Qubit", "T1", "T2")

STABLE = "Stable"
DEGRADING = "Degrading"


def analyze_qubit_data(df: pd.DataFrame) -> dict:
    """
    Validates, cleans, and analyzes a DataFrame of qubit readings.

    Steps: validate required columns -> drop exact duplicate rows -> detect
    missing values -> drop rows missing Qubit/T1/T2 -> compute QSFI and
    summary statistics -> assign a Stable/Degrading status to every qubit.

    Raises ValueError if a required column is missing or if no valid rows
    remain after cleaning.
    """
    _validate_required_columns(df)

    rows_before_dedup = len(df)
    df = df.drop_duplicates()
    duplicate_rows_removed = rows_before_dedup - len(df)

    missing_value_counts = _count_missing_values(df)

    rows_before_dropna = len(df)
    clean_df = df.dropna(subset=list(REQUIRED_COLUMNS)).copy()
    rows_with_missing_values_dropped = rows_before_dropna - len(clean_df)

    if clean_df.empty:
        raise ValueError("No valid rows remain after removing duplicates and missing values.")

    # QSFI is the blended stability index for a qubit: the midpoint of its
    # T1 (relaxation) and T2 (dephasing) readings.
    clean_df["QSFI"] = (clean_df["T1"] + clean_df["T2"]) / 2

    average_t1 = float(clean_df["T1"].mean())
    average_t2 = float(clean_df["T2"].mean())
    average_qsfi = float(clean_df["QSFI"].mean())

    best_row = clean_df.loc[clean_df["QSFI"].idxmax()]
    worst_row = clean_df.loc[clean_df["QSFI"].idxmin()]

    # A qubit is Stable if its QSFI is at or above the average across this
    # dataset, Degrading otherwise.
    clean_df["Status"] = np.where(clean_df["QSFI"] >= average_qsfi, STABLE, DEGRADING)

    qubits = [
        {
            "qubit": int(row["Qubit"]),
            "t1": float(row["T1"]),
            "t2": float(row["T2"]),
            "qsfi": float(row["QSFI"]),
            "status": row["Status"],
        }
        for _, row in clean_df.iterrows()
    ]

    return {
        "summary": {
            "total_qubits": int(clean_df["Qubit"].nunique()),
            "average_t1": average_t1,
            "average_t2": average_t2,
            "average_qsfi": average_qsfi,
            "best_qubit": {
                "qubit": int(best_row["Qubit"]),
                "qsfi": float(best_row["QSFI"]),
            },
            "worst_qubit": {
                "qubit": int(worst_row["Qubit"]),
                "qsfi": float(worst_row["QSFI"]),
            },
        },
        "data_quality": {
            "rows_received": rows_before_dedup,
            "duplicate_rows_removed": duplicate_rows_removed,
            "missing_values": missing_value_counts,
            "rows_with_missing_values_dropped": rows_with_missing_values_dropped,
            "rows_analyzed": int(len(clean_df)),
        },
        "qubits": qubits,
    }


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")


def _count_missing_values(df: pd.DataFrame) -> dict:
    """Number of missing (NaN/null) values in each required column."""
    return {col: int(df[col].isna().sum()) for col in REQUIRED_COLUMNS}
