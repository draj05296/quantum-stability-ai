"""Shared test helpers: fixture-data paths and analyzer-shaped record builders.

Two distinct shapes are involved, and mixing them up hides real behavior:

  - `make_analysis` -> exactly what services.analyzer returns (summary /
    data_quality / qubits, no provenance). This is what gets handed to
    `save_analysis_result`.
  - `make_saved_record` -> what ends up in processed/: the analyzer output
    plus the `analyzed_at` / `source_filename` fields history_service adds.
    This is what `compare_analyses` and `load_analysis` operate on.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "data"
DAY1_CSV = DATA_DIR / "quantum_data_day1.csv"
DAY3_CSV = DATA_DIR / "quantum_data_day3.csv"


def make_analysis(qubits, average_qsfi=None):
    """
    Builds a minimal services.analyzer result.

    `qubits` is a list of (qubit_id, qsfi, status) tuples; `average_qsfi`
    defaults to the mean of the given QSFI values. Only the fields the
    history/compare code actually reads carry meaningful values - the rest are
    present so the record keeps the real response shape.
    """
    qsfi_values = [qsfi for _, qsfi, _ in qubits]
    if average_qsfi is None:
        average_qsfi = sum(qsfi_values) / len(qsfi_values) if qsfi_values else 0.0

    return {
        "summary": {
            "total_qubits": len(qubits),
            "average_t1": 0.0,
            "average_t2": 0.0,
            "average_qsfi": average_qsfi,
            "best_qubit": {"qubit": 0, "qsfi": 0.0},
            "worst_qubit": {"qubit": 0, "qsfi": 0.0},
        },
        "data_quality": {
            "rows_received": len(qubits),
            "duplicate_rows_removed": 0,
            "missing_values": {"Qubit": 0, "T1": 0, "T2": 0},
            "rows_with_missing_values_dropped": 0,
            "rows_analyzed": len(qubits),
        },
        "qubits": [
            {"qubit": qubit_id, "t1": qsfi, "t2": qsfi, "qsfi": qsfi, "status": status}
            for qubit_id, qsfi, status in qubits
        ],
    }


def make_saved_record(
    qubits,
    average_qsfi=None,
    source_filename="source.csv",
    analyzed_at="2026-01-01T00:00:00+00:00",
):
    """Builds an analyzer result as services.history_service would have saved it."""
    return {
        "analyzed_at": analyzed_at,
        "source_filename": source_filename,
        **make_analysis(qubits, average_qsfi),
    }
