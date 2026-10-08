"""
Multi-day QSFI trend analysis.

This service retrieves saved analysis results and calculates:
- Day 1 -> latest QSFI percentage change
- QSFI trend slope across multiple days
- T1 trend slope
- T2 trend slope
- Each qubit's actual measured QSFI/T1/T2 history across the selected
  analyses (the `history` field), read directly from the saved records -
  never recalculated from raw CSVs, interpolated, or fabricated.

`days` selects unique research collection days, not raw database records: a
research day can have more than one saved analysis (e.g. a file re-uploaded
to fix a mistake), and these are collapsed to that day's most recently
analyzed record before anything else runs - see
_select_one_entry_per_collection_day().

The calculations are based on the saved per-qubit analysis results.
"""

import re

from services.history_service import list_analyses, load_analysis

# Matches the YYYY-MM-DD collection date embedded in a source filename, e.g.
# "quantum_data_week1_day5_2026-10-05.csv" -> "2026-10-05". Mirrors the same
# convention the frontend parses for chart labels
# (src/components/dashboard/TrendSection.jsx).
_COLLECTION_DAY_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _extract_collection_day(source_filename: str | None) -> str | None:
    """
    Returns the YYYY-MM-DD collection date embedded in `source_filename`, or
    None if it has no such date (e.g. the older "quantum_data_day1.csv"
    sample files, which predate this naming convention).
    """
    if not source_filename:
        return None

    match = _COLLECTION_DAY_PATTERN.search(source_filename)
    return match.group(1) if match else None


def _select_one_entry_per_collection_day(entries: list[dict]) -> list[dict]:
    """
    Collapses `entries` (as returned by list_analyses(): newest first, each
    with filename/analyzed_at/source_filename) to one entry per unique
    collection day, keeping the most recently analyzed record whenever a day
    has more than one saved analysis. Stays newest-first, like the input.

    Never deletes or modifies any saved record - this only changes which
    single record /trend reads to represent a day that was analyzed more
    than once. GET /history still lists every record.

    A source filename with no parseable collection date is treated as its
    own unique day (keyed by its own unique database filename instead of a
    date), so it's never merged with - or silently dropped in favor of -
    another record.
    """
    most_recent_entry_by_day = {}
    days_in_order = []

    for entry in entries:
        day_key = _extract_collection_day(entry.get("source_filename")) or entry["filename"]

        if day_key not in most_recent_entry_by_day:
            # `entries` is already newest-first, so the first entry seen for
            # a given day is already its most recently analyzed one; any
            # later (older) duplicate for the same day is simply skipped.
            most_recent_entry_by_day[day_key] = entry
            days_in_order.append(day_key)

    return [most_recent_entry_by_day[day_key] for day_key in days_in_order]


def get_trend_analysis(days: int = 5) -> dict:
    """
    Analyze the most recent unique collection days across multiple days.


    Returns per-qubit QSFI, T1, and T2 trends.
    """
    entries = _select_one_entry_per_collection_day(list_analyses())

    if len(entries) < 2:
        raise ValueError(
            f"At least two saved analyses are required for trend analysis; "
            f"found {len(entries)}."
        )

    # Take the requested number of newest unique collection days.
    selected_entries = entries[:days]

    # entries is newest first.
    # Reverse so calculations run chronologically: oldest -> newest.
    selected_entries.reverse()

    analyses = [
        load_analysis(entry["filename"])
        for entry in selected_entries
    ]

    # Match each analysis by qubit ID. Each reading also carries the actual
    # source filename/timestamp of the analysis it came from, so the full
    # measured history can be returned alongside the existing summary fields.
    # `analysis_filename` is the unique name this analysis was saved under
    # (from list_analyses(), aligned by index with `analyses`); `filename`
    # is the original uploaded CSV's name and can repeat across analyses
    # (e.g. the same file re-uploaded later) - the two are kept distinct.
    qubit_data = {}

    for day_index, analysis in enumerate(analyses):
        point_analysis_filename = selected_entries[day_index]["filename"]
        point_filename = analysis.get("source_filename")
        point_analyzed_at = analysis.get("analyzed_at")

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
                    "analysis_filename": point_analysis_filename,
                    "filename": point_filename,
                    "analyzed_at": point_analyzed_at,
                }
            )

    trends = []

    for qubit_id, readings in qubit_data.items():
        # Only analyze qubits available in every selected analysis. This is
        # unchanged from before `history` existed: a qubit missing from any
        # one selected analysis is excluded from `trends` entirely rather
        # than given a fabricated reading for the analysis it lacks, so every
        # qubit that does appear always has one real `history` point per
        # selected analysis - never a gap, never an invented value.
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

        # `readings` is already oldest -> latest: it was built by iterating
        # `analyses` (already reversed into that order) in sequence, so no
        # additional sort is needed here.
        history = [
            {
                "analysis_filename": reading["analysis_filename"],
                "filename": reading["filename"],
                "analyzed_at": reading["analyzed_at"],
                "qsfi": reading["qsfi"],
                "t1": reading["t1"],
                "t2": reading["t2"],
            }
            for reading in readings
        ]

        trends.append(
            {
                "qubit": qubit_id,
                "qsfi_day1": qsfi_values[0],
                "qsfi_latest": qsfi_values[-1],
                "qsfi_change_percent": qsfi_change_percent,
                "qsfi_slope": qsfi_slope,
                "t1_slope": t1_slope,
                "t2_slope": t2_slope,
                "history": history,
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

