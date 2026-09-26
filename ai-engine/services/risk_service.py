"""
Prototype early-instability risk analysis.

This service converts multi-day QSFI trends into a relative risk indicator.
The score is a project-defined heuristic and is not a validated probability
of quantum hardware failure.
"""

from services.trend_service import get_trend_analysis


def get_risk_analysis(days: int = 5) -> dict:
    """Calculate a prototype risk indicator for each tracked qubit."""

    trend_result = get_trend_analysis(days)

    risk_results = []

    for trend in trend_result["trends"]:
        decline_score = _decline_score(trend["qsfi_change_percent"])
        slope_score = _slope_score(trend["qsfi_slope"])
        parameter_score = _parameter_agreement_score(
            trend["t1_slope"],
            trend["t2_slope"],
        )

        risk_score = (
            (decline_score * 0.45)
            + (slope_score * 0.35)
            + (parameter_score * 0.20)
        )

        risk_results.append(
            {
                "qubit": trend["qubit"],
                "risk_score": round(risk_score, 2),
                "risk_level": _risk_level(risk_score),
                "qsfi_change_percent": trend["qsfi_change_percent"],
                "qsfi_slope": trend["qsfi_slope"],
                "t1_slope": trend["t1_slope"],
                "t2_slope": trend["t2_slope"],
            }
        )

    risk_results.sort(
        key=lambda item: item["risk_score"],
        reverse=True,
    )

    return {
        "days_analyzed": trend_result["days_analyzed"],
        "qubits_analyzed": trend_result["qubits_analyzed"],
        "oldest": trend_result["oldest"],
        "latest": trend_result["latest"],
        "risk_results": risk_results,
    }


def _decline_score(change_percent: float) -> float:
    """
    Convert QSFI percentage decline into a 0-100 severity score.

    A 50% or greater decline reaches the maximum score.
    """

    if change_percent >= 0:
        return 0.0

    score = (-change_percent / 50.0) * 100.0

    return _clamp(score)


def _slope_score(slope: float) -> float:
    """
    Convert a negative QSFI slope into a 0-100 severity score.

    A slope of -0.000020 or lower reaches the maximum score for
    this prototype dataset.
    """

    if slope >= 0:
        return 0.0

    score = (-slope / 0.000020) * 100.0

    return _clamp(score)


def _parameter_agreement_score(t1_slope: float, t2_slope: float) -> float:
    """Measure whether T1 and T2 are both moving downward."""

    t1_decreasing = t1_slope < 0
    t2_decreasing = t2_slope < 0

    if t1_decreasing and t2_decreasing:
        return 100.0

    if t1_decreasing or t2_decreasing:
        return 50.0

    return 0.0


def _risk_level(score: float) -> str:
    """Convert the prototype score into a simple risk category."""

    if score >= 60:
        return "High"

    if score >= 30:
        return "Moderate"

    return "Low"


def _clamp(value: float) -> float:
    """Keep a score between 0 and 100."""

    return max(0.0, min(100.0, value))