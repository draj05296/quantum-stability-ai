"""
Unit tests for services.compare_service.

`compare_analyses` is pure, so most tests hand it two hand-built records and
check the classification directly. The last section exercises
`get_latest_comparison` end-to-end through services.history_service, and one
test runs the two real CSVs through services.analyzer to confirm the
comparison holds up on production-shaped data.
"""

import json

import pandas as pd
import pytest

from services.analyzer import analyze_qubit_data
from services.compare_service import compare_analyses, get_latest_comparison
from services.history_service import save_analysis_result
from tests.helpers import DAY1_CSV, DAY3_CSV, make_analysis, make_saved_record


def qubit_ids(changes):
    return [change["qubit"] for change in changes]


# ---------------------------------------------------------------------------
# QSFI improved / degraded classification
# ---------------------------------------------------------------------------


def test_higher_qsfi_is_improved_lower_is_degraded_equal_is_neither():
    previous = make_saved_record([(0, 10.0, "Stable"), (1, 10.0, "Stable"), (2, 10.0, "Stable")])
    latest = make_saved_record([(0, 12.0, "Stable"), (1, 8.0, "Stable"), (2, 10.0, "Stable")])

    result = compare_analyses(previous, latest)

    assert qubit_ids(result["improved_qubits"]) == [0]
    assert qubit_ids(result["degraded_qubits"]) == [1]
    # Qubit 2 is unchanged, so it belongs in neither bucket.
    assert 2 not in qubit_ids(result["improved_qubits"]) + qubit_ids(result["degraded_qubits"])


def test_change_entries_carry_before_after_and_difference():
    previous = make_saved_record([(4, 10.0, "Stable")])
    latest = make_saved_record([(4, 17.5, "Stable")])

    (change,) = compare_analyses(previous, latest)["improved_qubits"]

    assert change == {
        "qubit": 4,
        "previous_qsfi": 10.0,
        "latest_qsfi": 17.5,
        "difference": pytest.approx(7.5),
    }


def test_degraded_difference_is_negative():
    previous = make_saved_record([(4, 10.0, "Stable")])
    latest = make_saved_record([(4, 4.0, "Stable")])

    (change,) = compare_analyses(previous, latest)["degraded_qubits"]

    assert change["difference"] == pytest.approx(-6.0)


# ---------------------------------------------------------------------------
# Stable / Degrading transitions
# ---------------------------------------------------------------------------


def test_status_transitions_are_reported_in_both_directions():
    previous = make_saved_record(
        [(0, 10.0, "Degrading"), (1, 10.0, "Stable"), (2, 10.0, "Stable"), (3, 10.0, "Degrading")]
    )
    latest = make_saved_record(
        [(0, 10.0, "Stable"), (1, 10.0, "Degrading"), (2, 10.0, "Stable"), (3, 10.0, "Degrading")]
    )

    result = compare_analyses(previous, latest)

    assert qubit_ids(result["newly_stable_qubits"]) == [0]
    assert qubit_ids(result["newly_unstable_qubits"]) == [1]
    # Qubits 2 and 3 kept their status, so neither is a transition.
    assert result["newly_stable_qubits"][0] == {
        "qubit": 0,
        "previous_status": "Degrading",
        "latest_status": "Stable",
    }


def test_status_transition_is_independent_of_the_qsfi_direction():
    """A qubit can become newly stable while its own QSFI drops - status is
    relative to that day's average, so both facts must be reported."""
    previous = make_saved_record([(0, 10.0, "Degrading")])
    latest = make_saved_record([(0, 9.0, "Stable")])

    result = compare_analyses(previous, latest)

    assert qubit_ids(result["degraded_qubits"]) == [0]
    assert qubit_ids(result["newly_stable_qubits"]) == [0]


# ---------------------------------------------------------------------------
# Qubit matching
# ---------------------------------------------------------------------------


def test_qubits_present_in_only_one_analysis_are_skipped():
    previous = make_saved_record([(0, 10.0, "Stable"), (1, 10.0, "Stable")])
    latest = make_saved_record([(1, 20.0, "Stable"), (2, 20.0, "Stable")])

    result = compare_analyses(previous, latest)

    assert result["qubits_compared"] == 1
    assert qubit_ids(result["improved_qubits"]) == [1]


def test_no_overlap_produces_an_empty_comparison():
    previous = make_saved_record([(0, 10.0, "Stable")])
    latest = make_saved_record([(9, 20.0, "Stable")])

    result = compare_analyses(previous, latest)

    assert result["qubits_compared"] == 0
    assert result["improved_qubits"] == []
    assert result["degraded_qubits"] == []
    assert result["newly_stable_qubits"] == []
    assert result["newly_unstable_qubits"] == []


def test_results_are_ordered_by_qubit_id():
    previous = make_saved_record([(9, 10.0, "Stable"), (2, 10.0, "Stable"), (5, 10.0, "Stable")])
    latest = make_saved_record([(9, 11.0, "Stable"), (2, 11.0, "Stable"), (5, 11.0, "Stable")])

    assert qubit_ids(compare_analyses(previous, latest)["improved_qubits"]) == [2, 5, 9]


def test_identical_analyses_report_no_changes():
    analysis = make_saved_record([(0, 10.0, "Stable"), (1, 5.0, "Degrading")])

    result = compare_analyses(analysis, json.loads(json.dumps(analysis)))

    assert result["qubits_compared"] == 2
    assert result["improved_qubits"] == []
    assert result["degraded_qubits"] == []
    assert result["newly_stable_qubits"] == []
    assert result["newly_unstable_qubits"] == []
    assert result["average_qsfi_change"]["difference"] == 0.0
    assert result["average_qsfi_change"]["percent_change"] == 0.0


# ---------------------------------------------------------------------------
# Average QSFI change
# ---------------------------------------------------------------------------


def test_average_qsfi_change_reports_difference_and_percent():
    previous = make_saved_record([(0, 10.0, "Stable")], average_qsfi=200.0)
    latest = make_saved_record([(0, 10.0, "Stable")], average_qsfi=150.0)

    change = compare_analyses(previous, latest)["average_qsfi_change"]

    assert change == {
        "previous": 200.0,
        "latest": 150.0,
        "difference": pytest.approx(-50.0),
        "percent_change": pytest.approx(-25.0),
    }


def test_zero_previous_average_does_not_divide_by_zero():
    previous = make_saved_record([(0, 0.0, "Stable")], average_qsfi=0.0)
    latest = make_saved_record([(0, 5.0, "Stable")], average_qsfi=5.0)

    change = compare_analyses(previous, latest)["average_qsfi_change"]

    assert change["difference"] == pytest.approx(5.0)
    assert change["percent_change"] == 0.0


# ---------------------------------------------------------------------------
# Provenance metadata
# ---------------------------------------------------------------------------


def test_previous_and_latest_reference_their_source_files():
    previous = make_saved_record(
        [(0, 1.0, "Stable")], source_filename="day1.csv", analyzed_at="2026-01-01T00:00:00+00:00"
    )
    latest = make_saved_record(
        [(0, 2.0, "Stable")], source_filename="day2.csv", analyzed_at="2026-01-02T00:00:00+00:00"
    )

    result = compare_analyses(previous, latest)

    assert result["previous"] == {
        "filename": "day1.csv",
        "analyzed_at": "2026-01-01T00:00:00+00:00",
    }
    assert result["latest"] == {"filename": "day2.csv", "analyzed_at": "2026-01-02T00:00:00+00:00"}


def test_missing_provenance_degrades_to_none_instead_of_raising():
    """Older saved records may predate the provenance fields."""
    previous = make_saved_record([(0, 1.0, "Stable")])
    latest = make_saved_record([(0, 2.0, "Stable")])
    del previous["source_filename"], previous["analyzed_at"]

    result = compare_analyses(previous, latest)

    assert result["previous"] == {"filename": None, "analyzed_at": None}


# ---------------------------------------------------------------------------
# get_latest_comparison (through services.history_service)
# ---------------------------------------------------------------------------


def test_get_latest_comparison_uses_the_two_newest_saved_analyses(temp_dirs):
    for name, qsfi, timestamp in [
        ("day1.csv", 10.0, "2026-01-01T00:00:00+00:00"),
        ("day2.csv", 20.0, "2026-01-02T00:00:00+00:00"),
        ("day3.csv", 30.0, "2026-01-03T00:00:00+00:00"),
    ]:
        record = make_saved_record([(0, qsfi, "Stable")], source_filename=name, analyzed_at=timestamp)
        (temp_dirs.processed / f"{name.removesuffix('.csv')}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )

    result = get_latest_comparison()

    # day1 is ignored - only the two most recent are compared.
    assert result["previous"]["filename"] == "day2.csv"
    assert result["latest"]["filename"] == "day3.csv"
    assert result["improved_qubits"][0]["difference"] == pytest.approx(10.0)


def test_get_latest_comparison_requires_two_saved_analyses(temp_dirs):
    save_analysis_result("day1.csv", make_analysis([(0, 1.0, "Stable")]))

    with pytest.raises(ValueError, match="At least two saved analyses"):
        get_latest_comparison()


# ---------------------------------------------------------------------------
# Real data (day1 vs day3)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def day1_vs_day3():
    previous = analyze_qubit_data(pd.read_csv(DAY1_CSV))
    latest = analyze_qubit_data(pd.read_csv(DAY3_CSV))
    return previous, latest, compare_analyses(previous, latest)


def test_day1_vs_day3_classification_matches_a_direct_recount(day1_vs_day3):
    """Recomputes the expected buckets straight from the two analyzer outputs."""
    previous, latest, result = day1_vs_day3
    previous_by_id = {q["qubit"]: q for q in previous["qubits"]}
    latest_by_id = {q["qubit"]: q for q in latest["qubits"]}
    common = sorted(set(previous_by_id) & set(latest_by_id))

    expected_improved = [q for q in common if latest_by_id[q]["qsfi"] > previous_by_id[q]["qsfi"]]
    expected_degraded = [q for q in common if latest_by_id[q]["qsfi"] < previous_by_id[q]["qsfi"]]
    expected_newly_stable = [
        q
        for q in common
        if previous_by_id[q]["status"] == "Degrading" and latest_by_id[q]["status"] == "Stable"
    ]
    expected_newly_unstable = [
        q
        for q in common
        if previous_by_id[q]["status"] == "Stable" and latest_by_id[q]["status"] == "Degrading"
    ]

    assert result["qubits_compared"] == len(common)
    assert qubit_ids(result["improved_qubits"]) == expected_improved
    assert qubit_ids(result["degraded_qubits"]) == expected_degraded
    assert qubit_ids(result["newly_stable_qubits"]) == expected_newly_stable
    assert qubit_ids(result["newly_unstable_qubits"]) == expected_newly_unstable


def test_day1_vs_day3_every_common_qubit_is_accounted_for(day1_vs_day3):
    """Day 1 and Day 3 differ on every qubit, so improved + degraded covers them all."""
    _, _, result = day1_vs_day3

    assert len(result["improved_qubits"]) + len(result["degraded_qubits"]) == result["qubits_compared"]
    assert result["qubits_compared"] > 0


def test_day1_vs_day3_average_change_matches_the_two_summaries(day1_vs_day3):
    previous, latest, result = day1_vs_day3
    change = result["average_qsfi_change"]

    assert change["previous"] == pytest.approx(previous["summary"]["average_qsfi"])
    assert change["latest"] == pytest.approx(latest["summary"]["average_qsfi"])
    assert change["difference"] == pytest.approx(change["latest"] - change["previous"])
    assert change["percent_change"] == pytest.approx(
        change["difference"] / change["previous"] * 100
    )
