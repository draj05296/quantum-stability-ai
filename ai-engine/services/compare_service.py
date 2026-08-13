"""
Compares two saved analysis results.

`compare_analyses` is pure (plain dicts in, plain dict out, no I/O) so it
can be tested in isolation; `get_latest_comparison` is the thin orchestration
that fetches the two most recent saved analyses from services.history_service
and hands them to it.
"""

from services.history_service import get_two_most_recent_analyses


def get_latest_comparison() -> dict:
    """Loads the two most recent saved analyses and compares them."""
    previous, latest = get_two_most_recent_analyses()
    return compare_analyses(previous, latest)


def compare_analyses(previous: dict, latest: dict) -> dict:
    """
    Compares two services.analyzer results (as saved by
    services.history_service) qubit-by-qubit, matching on qubit id.

    Qubits present in only one of the two analyses are skipped - there's
    nothing to compare them against.
    """
    previous_qubits = {q["qubit"]: q for q in previous["qubits"]}
    latest_qubits = {q["qubit"]: q for q in latest["qubits"]}
    common_qubit_ids = sorted(set(previous_qubits) & set(latest_qubits))

    improved_qubits = []
    degraded_qubits = []
    newly_stable_qubits = []
    newly_unstable_qubits = []

    for qubit_id in common_qubit_ids:
        before = previous_qubits[qubit_id]
        after = latest_qubits[qubit_id]

        if after["qsfi"] > before["qsfi"]:
            improved_qubits.append(_qubit_change(qubit_id, before["qsfi"], after["qsfi"]))
        elif after["qsfi"] < before["qsfi"]:
            degraded_qubits.append(_qubit_change(qubit_id, before["qsfi"], after["qsfi"]))

        if before["status"] == "Degrading" and after["status"] == "Stable":
            newly_stable_qubits.append(_status_change(qubit_id, before["status"], after["status"]))
        elif before["status"] == "Stable" and after["status"] == "Degrading":
            newly_unstable_qubits.append(_status_change(qubit_id, before["status"], after["status"]))

    return {
        "previous": {
            "filename": previous.get("source_filename"),
            "analyzed_at": previous.get("analyzed_at"),
        },
        "latest": {
            "filename": latest.get("source_filename"),
            "analyzed_at": latest.get("analyzed_at"),
        },
        "qubits_compared": len(common_qubit_ids),
        "average_qsfi_change": _qsfi_summary_change(
            previous["summary"]["average_qsfi"], latest["summary"]["average_qsfi"]
        ),
        "improved_qubits": improved_qubits,
        "degraded_qubits": degraded_qubits,
        "newly_stable_qubits": newly_stable_qubits,
        "newly_unstable_qubits": newly_unstable_qubits,
    }


def _qubit_change(qubit_id: int, previous_qsfi: float, latest_qsfi: float) -> dict:
    return {
        "qubit": qubit_id,
        "previous_qsfi": previous_qsfi,
        "latest_qsfi": latest_qsfi,
        "difference": latest_qsfi - previous_qsfi,
    }


def _status_change(qubit_id: int, previous_status: str, latest_status: str) -> dict:
    return {
        "qubit": qubit_id,
        "previous_status": previous_status,
        "latest_status": latest_status,
    }


def _qsfi_summary_change(previous_avg: float, latest_avg: float) -> dict:
    difference = latest_avg - previous_avg
    percent_change = (difference / previous_avg * 100) if previous_avg != 0 else 0.0

    return {
        "previous": previous_avg,
        "latest": latest_avg,
        "difference": difference,
        "percent_change": percent_change,
    }
