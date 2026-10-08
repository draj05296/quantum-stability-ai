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
from services.trend_service import (
    _extract_collection_day,
    _select_one_entry_per_collection_day,
    get_trend_analysis,
)


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
    each entry carrying filename/analyzed_at/source_filename, with
    load_analysis looking a record up by its filename) without a database.

    Entries are only appended here, never reordered or deduplicated - that
    collapsing is get_trend_analysis's job (via
    _select_one_entry_per_collection_day), and the point of this helper is
    to hand it a realistic, undeduplicated list to collapse.
    """
    registry = {}
    for index, analysis in enumerate(analyses_oldest_first):
        filename = f"saved_{index}.json"
        registry[filename] = analysis

    entries_newest_first = [
        {
            "filename": f"saved_{index}.json",
            "analyzed_at": analysis["analyzed_at"],
            "source_filename": analysis["source_filename"],
        }
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


# ---------------------------------------------------------------------------
# 8. Duplicate analyses for the SAME research collection day (identified by
#    the date embedded in the source filename) collapse to one entry - the
#    most recently analyzed record for that day - so `days` counts unique
#    collection days rather than raw database records.
# ---------------------------------------------------------------------------


def _dated_analysis(day_label, date, analyzed_at, qsfi):
    """A saved analysis whose source filename embeds its real collection date."""
    return _analysis(
        f"quantum_data_week1_{day_label}_{date}.csv",
        analyzed_at,
        [(0, qsfi, qsfi, qsfi)],
    )


def test_duplicate_analyses_for_the_same_collection_day_use_the_most_recent(monkeypatch):
    """
    Mirrors the real /history state this fix was written for: Day 1 and
    Day 5 each have two saved analyses (e.g. a re-upload), every other day
    has one, and Oct 4 was never collected at all.

    Supplied in true chronological (oldest analyzed_at -> latest) order, as
    _install_fake_history requires.
    """
    analyses = [
        # _install_fake_history requires true chronological (analyzed_at
        # ascending) order, exactly like the real list_analyses() guarantees
        # via its own ORDER BY - a re-upload's later analyzed_at must appear
        # after its original here, not merely be adjacent to it in list order.
        _dated_analysis("day1", "2026-09-29", "2026-09-29T09:00:00+00:00", 10.0),  # Day 1, first upload
        _dated_analysis("day1", "2026-09-29", "2026-09-29T15:00:00+00:00", 10.5),  # Day 1, RE-upload (most recent for that day)
        _dated_analysis("day2", "2026-10-01", "2026-10-01T09:00:00+00:00", 11.0),  # Day 2
        _dated_analysis("day3", "2026-10-02", "2026-10-02T09:00:00+00:00", 12.0),  # Day 3
        _dated_analysis("day4", "2026-10-03", "2026-10-03T09:00:00+00:00", 13.0),  # Day 4
        _dated_analysis("day5", "2026-10-05", "2026-10-05T09:00:00+00:00", 14.0),  # Day 5, first upload
        _dated_analysis("day5", "2026-10-05", "2026-10-05T18:00:00+00:00", 14.5),  # Day 5, RE-upload (most recent for that day)
        _dated_analysis("day6", "2026-10-06", "2026-10-06T09:00:00+00:00", 15.0),  # Day 6
        _dated_analysis("day7", "2026-10-07", "2026-10-07T09:00:00+00:00", 16.0),  # Day 7
    ]
    _install_fake_history(monkeypatch, analyses)

    # days=7 must cover all 7 UNIQUE collection days (9 raw records), using
    # each duplicated day's most recently analyzed record, in chronological
    # order, with no fabricated Oct 4 entry in between.
    result = get_trend_analysis(days=7)
    (trend,) = result["trends"]

    assert result["days_analyzed"] == 7
    assert [p["qsfi"] for p in trend["history"]] == [
        10.5,  # Day 1 - the 15:00 re-upload won, not the 09:00 original
        11.0,  # Day 2
        12.0,  # Day 3
        13.0,  # Day 4
        14.5,  # Day 5 - the 18:00 re-upload won, not the 09:00 original
        15.0,  # Day 6
        16.0,  # Day 7
    ]
    assert [p["filename"] for p in trend["history"]] == [
        "quantum_data_week1_day1_2026-09-29.csv",
        "quantum_data_week1_day2_2026-10-01.csv",
        "quantum_data_week1_day3_2026-10-02.csv",
        "quantum_data_week1_day4_2026-10-03.csv",
        "quantum_data_week1_day5_2026-10-05.csv",
        "quantum_data_week1_day6_2026-10-06.csv",
        "quantum_data_week1_day7_2026-10-07.csv",
    ]
    # No entry anywhere references an Oct 4 collection - none exists.
    assert all("2026-10-04" not in (p["filename"] or "") for p in trend["history"])


def test_days_parameter_counts_unique_collection_days_not_raw_records(monkeypatch):
    """days=5 against the same 9-record/7-day history must select the 5
    most recent UNIQUE days (Day 3-7), not the 5 most recent raw records
    (which would wrongly include both Day 5 duplicates and only reach back
    to Day 4)."""
    analyses = [
        _dated_analysis("day1", "2026-09-29", "2026-09-29T09:00:00+00:00", 10.0),
        _dated_analysis("day1", "2026-09-29", "2026-09-29T15:00:00+00:00", 10.5),
        _dated_analysis("day2", "2026-10-01", "2026-10-01T09:00:00+00:00", 11.0),
        _dated_analysis("day3", "2026-10-02", "2026-10-02T09:00:00+00:00", 12.0),
        _dated_analysis("day4", "2026-10-03", "2026-10-03T09:00:00+00:00", 13.0),
        _dated_analysis("day5", "2026-10-05", "2026-10-05T09:00:00+00:00", 14.0),
        _dated_analysis("day5", "2026-10-05", "2026-10-05T18:00:00+00:00", 14.5),
        _dated_analysis("day6", "2026-10-06", "2026-10-06T09:00:00+00:00", 15.0),
        _dated_analysis("day7", "2026-10-07", "2026-10-07T09:00:00+00:00", 16.0),
    ]
    _install_fake_history(monkeypatch, analyses)

    result = get_trend_analysis(days=5)
    (trend,) = result["trends"]

    assert result["days_analyzed"] == 5
    assert [p["qsfi"] for p in trend["history"]] == [12.0, 13.0, 14.5, 15.0, 16.0]
    assert [p["filename"] for p in trend["history"]] == [
        "quantum_data_week1_day3_2026-10-02.csv",
        "quantum_data_week1_day4_2026-10-03.csv",
        "quantum_data_week1_day5_2026-10-05.csv",
        "quantum_data_week1_day6_2026-10-06.csv",
        "quantum_data_week1_day7_2026-10-07.csv",
    ]


def test_collection_day_deduplication_does_not_change_history_record_count(monkeypatch):
    """
    The dedup is purely a selection concern inside trend_service -
    list_analyses() (what GET /history reports) must still return every raw
    record untouched.
    """
    analyses = [
        _dated_analysis("day1", "2026-09-29", "2026-09-29T09:00:00+00:00", 10.0),
        _dated_analysis("day1", "2026-09-29", "2026-09-29T15:00:00+00:00", 10.5),
        _dated_analysis("day2", "2026-10-01", "2026-10-01T09:00:00+00:00", 11.0),
    ]
    _install_fake_history(monkeypatch, analyses)

    # trend_service.list_analyses must be referenced dynamically (via the
    # module, not a `from ... import` snapshot taken before patching) so it
    # reflects what _install_fake_history just patched.
    assert len(trend_service.list_analyses()) == 3


# ---------------------------------------------------------------------------
# Pure unit tests for the two new helpers, independent of get_trend_analysis.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source_filename", "expected"),
    [
        ("quantum_data_week1_day5_2026-10-05.csv", "2026-10-05"),
        ("quantum_data_week1_day1_2026-09-29.csv", "2026-09-29"),
        ("quantum_data_day1.csv", None),  # older, pre-dated-convention file
        (None, None),
    ],
)
def test_extract_collection_day(source_filename, expected):
    assert _extract_collection_day(source_filename) == expected


def test_select_one_entry_per_collection_day_keeps_the_newest_duplicate():
    # Newest-first, as list_analyses() returns it.
    entries = [
        {"filename": "b.json", "analyzed_at": "2026-09-29T15:00:00+00:00",
         "source_filename": "quantum_data_week1_day1_2026-09-29.csv"},
        {"filename": "c.json", "analyzed_at": "2026-10-01T09:00:00+00:00",
         "source_filename": "quantum_data_week1_day2_2026-10-01.csv"},
        {"filename": "a.json", "analyzed_at": "2026-09-29T09:00:00+00:00",
         "source_filename": "quantum_data_week1_day1_2026-09-29.csv"},
    ]

    result = _select_one_entry_per_collection_day(entries)

    # Still newest-first; Day 1's older 09:00 duplicate ("a.json") is gone,
    # only the newer 15:00 one ("b.json") represents that day.
    assert [e["filename"] for e in result] == ["b.json", "c.json"]


def test_select_one_entry_per_collection_day_is_a_no_op_without_duplicates():
    entries = [
        {"filename": "b.json", "analyzed_at": "2026-10-01T09:00:00+00:00",
         "source_filename": "quantum_data_week1_day2_2026-10-01.csv"},
        {"filename": "a.json", "analyzed_at": "2026-09-29T09:00:00+00:00",
         "source_filename": "quantum_data_week1_day1_2026-09-29.csv"},
    ]

    assert _select_one_entry_per_collection_day(entries) == entries


def test_select_one_entry_per_collection_day_handles_empty_list():
    assert _select_one_entry_per_collection_day([]) == []
