"""
Unit tests for the historical-series addition to services.trend_service, and
a regression check that services.risk_service still works against the
extended response.

None of these tests touch a real database: services.trend_service imports
`list_analyses`/`load_analysis` by name from services.history_service, so
patching those two names on the trend_service module is enough to control
exactly what "saved analyses" the service sees, with no psycopg connection
ever attempted. This is also why DATABASE_URL only needs to be *set* (see
conftest.py) rather than pointing at a real database for these tests.
"""

import pytest

import services.trend_service as trend_service
from services.risk_service import get_risk_analysis
from services.trend_service import get_trend_analysis


def _analysis(source_filename, analyzed_at, qubits):
    """
    Builds a minimal saved-analysis record as services.trend_service reads
    it: only `source_filename`, `analyzed_at`, and `qubits` are ever
    accessed by get_trend_analysis.

    `qubits` is a list of (qubit_id, qsfi, t1, t2) tuples, independently
    controllable (unlike tests.helpers.make_saved_record, which always sets
    t1 == t2 == qsfi) so T1/T2 slopes can be tested separately from QSFI.
    """
    return {
        "source_filename": source_filename,
        "analyzed_at": analyzed_at,
        "qubits": [
            {"qubit": qubit_id, "qsfi": qsfi, "t1": t1, "t2": t2, "status": "Stable"}
            for qubit_id, qsfi, t1, t2 in qubits
        ],
    }


def _install_fake_history(monkeypatch, analyses_oldest_first):
    """
    Registers a fixed set of saved analyses and patches trend_service's
    list_analyses/load_analysis to serve them, mimicking
    services.history_service's real contract (list_analyses newest-first,
    each entry naming a filename load_analysis can look up) without a
    database.
    """
    registry = {}
    for index, analysis in enumerate(analyses_oldest_first):
        filename = f"saved_{index}.json"
        registry[filename] = analysis

    entries_newest_first = [
        {"filename": f"saved_{index}.json", "analyzed_at": analysis["analyzed_at"]}
        for index, analysis in enumerate(analyses_oldest_first)
    ][::-1]

    monkeypatch.setattr(trend_service, "list_analyses", lambda: entries_newest_first)
    monkeypatch.setattr(trend_service, "load_analysis", lambda filename: registry[filename])


# ---------------------------------------------------------------------------
# 1 & 4. Multiple analyses -> multiple chronological history points,
#        existing summary fields remain present and correctly computed.
# ---------------------------------------------------------------------------


def test_multiple_analyses_produce_chronological_history_points(monkeypatch):
    analyses = [
        _analysis("day1.csv", "2026-01-01T00:00:00+00:00", [(0, 10.0, 8.0, 12.0)]),
        _analysis("day2.csv", "2026-01-02T00:00:00+00:00", [(0, 12.0, 9.0, 15.0)]),
        _analysis("day3.csv", "2026-01-03T00:00:00+00:00", [(0, 14.0, 10.0, 18.0)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    result = get_trend_analysis(days=3)

    # Existing summary fields are all still present.
    assert result["days_analyzed"] == 3
    assert result["qubits_analyzed"] == 1
    assert result["oldest"] == {"filename": "day1.csv", "analyzed_at": "2026-01-01T00:00:00+00:00"}
    assert result["latest"] == {"filename": "day3.csv", "analyzed_at": "2026-01-03T00:00:00+00:00"}

    (trend,) = result["trends"]
    assert trend["qubit"] == 0
    assert trend["qsfi_day1"] == pytest.approx(10.0)
    assert trend["qsfi_latest"] == pytest.approx(14.0)
    assert trend["qsfi_change_percent"] == pytest.approx(40.0)

    # The new field: three real points, oldest -> latest.
    history = trend["history"]
    assert len(history) == 3
    assert [p["filename"] for p in history] == ["day1.csv", "day2.csv", "day3.csv"]
    assert [p["analyzed_at"] for p in history] == [
        "2026-01-01T00:00:00+00:00",
        "2026-01-02T00:00:00+00:00",
        "2026-01-03T00:00:00+00:00",
    ]


# ---------------------------------------------------------------------------
# 2. Historical QSFI/T1/T2 values match the saved analysis records exactly.
# ---------------------------------------------------------------------------


def test_history_values_match_the_saved_records_exactly(monkeypatch):
    analyses = [
        _analysis("day1.csv", "2026-01-01T00:00:00+00:00", [(5, 0.00011, 0.00009, 0.00013)]),
        _analysis("day2.csv", "2026-01-02T00:00:00+00:00", [(5, 0.00017, 0.00014, 0.00020)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    (trend,) = get_trend_analysis(days=2)["trends"]
    history = trend["history"]

    assert history[0] == {
        "analysis_filename": "saved_0.json",
        "filename": "day1.csv",
        "analyzed_at": "2026-01-01T00:00:00+00:00",
        "qsfi": 0.00011,
        "t1": 0.00009,
        "t2": 0.00013,
    }
    assert history[1] == {
        "analysis_filename": "saved_1.json",
        "filename": "day2.csv",
        "analyzed_at": "2026-01-02T00:00:00+00:00",
        "qsfi": 0.00017,
        "t1": 0.00014,
        "t2": 0.00020,
    }


# ---------------------------------------------------------------------------
# 3. A qubit missing from one analysis is excluded, never fabricated.
# ---------------------------------------------------------------------------


def test_qubit_missing_from_one_analysis_is_excluded_not_fabricated(monkeypatch):
    analyses = [
        _analysis("day1.csv", "2026-01-01T00:00:00+00:00", [(0, 10.0, 10.0, 10.0), (7, 5.0, 5.0, 5.0)]),
        # Qubit 7 is absent from this analysis entirely.
        _analysis("day2.csv", "2026-01-02T00:00:00+00:00", [(0, 11.0, 11.0, 11.0)]),
        _analysis("day3.csv", "2026-01-03T00:00:00+00:00", [(0, 12.0, 12.0, 12.0), (7, 6.0, 6.0, 6.0)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    result = get_trend_analysis(days=3)
    trends_by_qubit = {t["qubit"]: t for t in result["trends"]}

    # Qubit 7 never gets a fabricated day2 reading - it's excluded outright.
    assert 7 not in trends_by_qubit
    assert result["qubits_analyzed"] == 1

    # Qubit 0, present everywhere, has exactly 3 real (non-fabricated) points.
    history = trends_by_qubit[0]["history"]
    assert [p["qsfi"] for p in history] == [10.0, 11.0, 12.0]


# ---------------------------------------------------------------------------
# 5. /risk still works, unaffected by the new `history` field.
# ---------------------------------------------------------------------------


def test_risk_analysis_still_works_and_never_sees_history(monkeypatch):
    # Two qubits: one with a clear QSFI decline on both T1 and T2 (should
    # score High), one flat (should score Low) - the same shape used to
    # validate risk_service before this change.
    analyses = [
        _analysis(
            "day1.csv",
            "2026-01-01T00:00:00+00:00",
            [(0, 100.0, 100.0, 100.0), (1, 50.0, 50.0, 50.0)],
        ),
        _analysis(
            "day2.csv",
            "2026-01-02T00:00:00+00:00",
            [(0, 40.0, 40.0, 40.0), (1, 50.0, 50.0, 50.0)],
        ),
    ]
    _install_fake_history(monkeypatch, analyses)

    risk = get_risk_analysis(days=2)

    assert risk["days_analyzed"] == 2
    assert risk["qubits_analyzed"] == 2

    results_by_qubit = {r["qubit"]: r for r in risk["risk_results"]}

    # Qubit 0: -60% change, both T1 and T2 declining -> maxes out at High.
    assert results_by_qubit[0]["risk_level"] == "High"
    assert results_by_qubit[0]["risk_score"] == pytest.approx(100.0)

    # Qubit 1: no change at all -> Low, zero score.
    assert results_by_qubit[1]["risk_level"] == "Low"
    assert results_by_qubit[1]["risk_score"] == pytest.approx(0.0)

    # risk_results is still exactly the pre-existing shape - `history` from
    # the extended trend items must never leak into the risk response.
    for entry in risk["risk_results"]:
        assert set(entry) == {
            "qubit",
            "risk_score",
            "risk_level",
            "qsfi_change_percent",
            "qsfi_slope",
            "t1_slope",
            "t2_slope",
        }


# ---------------------------------------------------------------------------
# 6. Insufficient historical data is still handled correctly.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("analysis_count", [0, 1])
def test_fewer_than_two_analyses_still_raises_value_error(monkeypatch, analysis_count):
    analyses = [
        _analysis(f"day{i}.csv", f"2026-01-0{i + 1}T00:00:00+00:00", [(0, 1.0, 1.0, 1.0)])
        for i in range(analysis_count)
    ]
    _install_fake_history(monkeypatch, analyses)

    with pytest.raises(ValueError, match=f"found {analysis_count}"):
        get_trend_analysis(days=5)


# ---------------------------------------------------------------------------
# 7. Duplicate uploads of the same source file are kept as separate,
#    legitimate measurements - never merged or discarded.
# ---------------------------------------------------------------------------


def test_duplicate_source_filename_uploads_are_both_kept(monkeypatch):
    analyses = [
        _analysis("quantum_data_day1.csv", "2026-01-01T00:00:00+00:00", [(0, 10.0, 10.0, 10.0)]),
        # Re-uploading the same source file later is a distinct, legitimate
        # measurement event (a different analyzed_at, and possibly different
        # values) - not a duplicate to be collapsed.
        _analysis("quantum_data_day1.csv", "2026-01-05T00:00:00+00:00", [(0, 9.0, 9.0, 9.0)]),
        _analysis("quantum_data_day2.csv", "2026-01-06T00:00:00+00:00", [(0, 8.0, 8.0, 8.0)]),
    ]
    _install_fake_history(monkeypatch, analyses)

    (trend,) = get_trend_analysis(days=3)["trends"]
    history = trend["history"]

    assert len(history) == 3
    assert [p["filename"] for p in history] == [
        "quantum_data_day1.csv",
        "quantum_data_day1.csv",
        "quantum_data_day2.csv",
    ]
    # Both quantum_data_day1.csv points survive as separate entries, each
    # with its own timestamp and value - neither was discarded or merged.
    assert history[0]["analyzed_at"] != history[1]["analyzed_at"]
    assert history[0]["qsfi"] != history[1]["qsfi"]
