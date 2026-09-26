"""
Multi-day QSFI trend analysis.

This service retrieves saved analysis results and calculates:
- Day 1 -> latest QSFI percentage change
- QSFI trend slope across multiple days
- T1 trend slope
- T2 trend slope

The calculations are based on the saved per-qubit analysis results.
"""

from services.history_service import list_analyses, load_analysis


def get_trend_analysis(days: int = 5) -> dict:
    """
    Analyze the most recent saved analyses across multiple days.


    Returns per-qubit QSFI, T1, and T2 trends.
    """
    entries = list_analyses()

    if len(entries) < 2:
        raise ValueError(
            f"At least two saved analyses are required for trend analysis; "
            f"found {len(entries)}."
        )

    # Take the requested number of newest analyses.
    selected_entries = entries[:days]

    # list_analyses() returns newest first.
    # Reverse so calculations run chronologically: oldest -> newest.
    selected_entries.reverse()

    analyses = [
        load_analysis(entry["filename"])
        for entry in selected_entries
    ]

    # Match each analysis by qubit ID.
    qubit_data = {}

    for day_index, analysis in enumerate(analyses):
        for qubit in analysis["qubits"]:
            qubit_id = qubit["qubit"]

            if qubit_id not in qubit_data:
                qubit_data[qubit_id] = []

            qubit_data[qubit_id].append(
                {
                    "day": day_index + 1,
                    "qsfi": qubit["qsfi"],
                    "t1": qubit["t1"],
                    "t2": qubit["t2"],
                }
            )

    trends = []

    for qubit_id, readings in qubit_data.items():
        # Only analyze qubits available in every selected analysis.
        if len(readings) != len(analyses):
            continue

        qsfi_values = [reading["qsfi"] for reading in readings]
        t1_values = [reading["t1"] for reading in readings]
        t2_values = [reading["t2"] for reading in readings]

        qsfi_change_percent = _percentage_change(
            qsfi_values[0],
            qsfi_values[-1],
        )

        qsfi_slope = _linear_slope(qsfi_values)
        t1_slope = _linear_slope(t1_values)
        t2_slope = _linear_slope(t2_values)

        trends.append(
            {
                "qubit": qubit_id,
                "qsfi_day1": qsfi_values[0],
                "qsfi_latest": qsfi_values[-1],
                "qsfi_change_percent": qsfi_change_percent,
                "qsfi_slope": qsfi_slope,
                "t1_slope": t1_slope,
                "t2_slope": t2_slope,
            }
        )

    trends.sort(key=lambda item: item["qsfi_slope"])

    return {
        "days_analyzed": len(analyses),
        "qubits_analyzed": len(trends),
        "oldest": {
            "filename": analyses[0].get("source_filename"),
            "analyzed_at": analyses[0].get("analyzed_at"),
        },
        "latest": {
            "filename": analyses[-1].get("source_filename"),
            "analyzed_at": analyses[-1].get("analyzed_at"),
        },
        "trends": trends,
    }


def _percentage_change(previous: float, latest: float) -> float:
    """Calculate percentage change from the first value to the latest."""
    if previous == 0:
        return 0.0

    return ((latest - previous) / previous) * 100


def _linear_slope(values: list[float]) -> float:
    """
    Calculate the linear trend slope across equally spaced observations.

    A negative value indicates an overall downward trend.
    A positive value indicates an overall upward trend.
    """
    if len(values) < 2:
        return 0.0

    n = len(values)

    x_values = list(range(1, n + 1))
    x_mean = sum(x_values) / n
    y_mean = sum(values) / n

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, values)
    )

    denominator = sum(
        (x - x_mean) ** 2
        for x in x_values
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator

