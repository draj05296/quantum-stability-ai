"""
Unit tests for services.analyzer.

Two kinds of coverage:
  - Integration-style tests against the real quantum_data_day1.csv, checked
    against ground-truth values computed independently with plain pandas
    (not hardcoded numbers) so the assertions stay correct even if the
    fixture data changes.
  - Small synthetic-DataFrame tests that isolate one behavior each
    (duplicates, missing values, status boundary, error cases).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from services.analyzer import analyze_qubit_data

DAY1_CSV = Path(__file__).resolve().parent.parent.parent / "src" / "data" / "quantum_data_day1.csv"


@pytest.fixture(scope="module")
def day1_raw_df():
    return pd.read_csv(DAY1_CSV)


@pytest.fixture(scope="module")
def day1_result(day1_raw_df):
    return analyze_qubit_data(day1_raw_df.copy())


@pytest.fixture(scope="module")
def day1_ground_truth(day1_raw_df):
    """Recomputes every expected value directly with pandas, independent of analyzer.py."""
    clean = day1_raw_df.drop_duplicates().dropna(subset=["Qubit", "T1", "T2"])
    qsfi = (clean["T1"] + clean["T2"]) / 2
    avg_qsfi = qsfi.mean()

    return {
        "rows_analyzed": len(clean),
        "total_qubits": clean["Qubit"].nunique(),
        "average_t1": clean["T1"].mean(),
        "average_t2": clean["T2"].mean(),
        "average_qsfi": avg_qsfi,
        "best_qubit": int(clean.loc[qsfi.idxmax(), "Qubit"]),
        "best_qsfi": qsfi.max(),
        "worst_qubit": int(clean.loc[qsfi.idxmin(), "Qubit"]),
        "worst_qsfi": qsfi.min(),
        "stable_count": int((qsfi >= avg_qsfi).sum()),
        "degrading_count": int((qsfi < avg_qsfi).sum()),
    }


# ---------------------------------------------------------------------------
# Real-data tests (quantum_data_day1.csv)
# ---------------------------------------------------------------------------


def test_day1_summary_matches_ground_truth(day1_result, day1_ground_truth):
    summary = day1_result["summary"]

    assert summary["total_qubits"] == day1_ground_truth["total_qubits"]
    assert summary["average_t1"] == pytest.approx(day1_ground_truth["average_t1"])
    assert summary["average_t2"] == pytest.approx(day1_ground_truth["average_t2"])
    assert summary["average_qsfi"] == pytest.approx(day1_ground_truth["average_qsfi"])
    assert summary["best_qubit"]["qubit"] == day1_ground_truth["best_qubit"]
    assert summary["best_qubit"]["qsfi"] == pytest.approx(day1_ground_truth["best_qsfi"])
    assert summary["worst_qubit"]["qubit"] == day1_ground_truth["worst_qubit"]
    assert summary["worst_qubit"]["qsfi"] == pytest.approx(day1_ground_truth["worst_qsfi"])


def test_day1_data_quality_matches_known_file_contents(day1_result, day1_ground_truth):
    # day1.csv is known to have 156 raw rows, 0 duplicates, and exactly one
    # missing T2 value (Qubit 72).
    quality = day1_result["data_quality"]

    assert quality["rows_received"] == 156
    assert quality["duplicate_rows_removed"] == 0
    assert quality["missing_values"] == {"Qubit": 0, "T1": 0, "T2": 1}
    assert quality["rows_with_missing_values_dropped"] == 1
    assert quality["rows_analyzed"] == day1_ground_truth["rows_analyzed"]


def test_day1_qubit_count_and_stable_degrading_split(day1_result, day1_ground_truth):
    qubits = day1_result["qubits"]
    assert len(qubits) == day1_ground_truth["rows_analyzed"]

    stable = [q for q in qubits if q["status"] == "Stable"]
    degrading = [q for q in qubits if q["status"] == "Degrading"]

    assert len(stable) == day1_ground_truth["stable_count"]
    assert len(degrading) == day1_ground_truth["degrading_count"]
    assert len(stable) + len(degrading) == len(qubits)


def test_day1_every_qubit_status_is_correct(day1_result):
    """Every single row's status must agree with the >= average_qsfi rule, not just the totals."""
    average_qsfi = day1_result["summary"]["average_qsfi"]

    for entry in day1_result["qubits"]:
        expected_status = "Stable" if entry["qsfi"] >= average_qsfi else "Degrading"
        assert entry["status"] == expected_status
        assert entry["qsfi"] == pytest.approx((entry["t1"] + entry["t2"]) / 2)


def test_day1_missing_row_excluded_from_results(day1_result):
    """Qubit 72 (the row with a missing T2) must not appear in the cleaned output."""
    qubit_ids = [entry["qubit"] for entry in day1_result["qubits"]]
    assert 72 not in qubit_ids


def test_day1_result_is_json_serializable(day1_result):
    """Confirms the 'JSON-ready dictionary' requirement concretely, not just by convention."""
    serialized = json.dumps(day1_result)
    assert json.loads(serialized) == day1_result


def test_day1_qubit_ids_are_native_python_ints(day1_result):
    for entry in day1_result["qubits"]:
        assert isinstance(entry["qubit"], int)
        assert not isinstance(entry["qubit"], np.integer)

    # best_qubit/worst_qubit are pulled from a single-row Series selection
    # (clean_df.loc[idxmax()]), which pandas can upcast to float64 when the
    # row mixes int/float columns - assert the int type explicitly here
    # since `5.0 == 5` would silently hide a regression back to float.
    best_qubit_id = day1_result["summary"]["best_qubit"]["qubit"]
    worst_qubit_id = day1_result["summary"]["worst_qubit"]["qubit"]
    assert isinstance(best_qubit_id, int) and not isinstance(best_qubit_id, bool)
    assert isinstance(worst_qubit_id, int) and not isinstance(worst_qubit_id, bool)


# ---------------------------------------------------------------------------
# Synthetic-data tests (isolate one behavior each)
# ---------------------------------------------------------------------------


def test_missing_required_column_raises_value_error():
    df = pd.DataFrame({"Qubit": [0, 1], "T1": [1.0, 2.0]})  # T2 missing entirely

    with pytest.raises(ValueError, match="T2"):
        analyze_qubit_data(df)


def test_duplicate_rows_are_removed():
    df = pd.DataFrame(
        {
            "Qubit": [0, 0, 1],
            "T1": [10.0, 10.0, 20.0],
            "T2": [10.0, 10.0, 20.0],
        }
    )

    result = analyze_qubit_data(df)

    assert result["data_quality"]["duplicate_rows_removed"] == 1
    assert result["data_quality"]["rows_analyzed"] == 2
    assert result["summary"]["total_qubits"] == 2


def test_missing_values_are_detected_and_dropped():
    df = pd.DataFrame(
        {
            "Qubit": [0, 1, 2],
            "T1": [10.0, np.nan, 30.0],
            "T2": [10.0, 20.0, np.nan],
        }
    )

    result = analyze_qubit_data(df)

    assert result["data_quality"]["missing_values"] == {"Qubit": 0, "T1": 1, "T2": 1}
    assert result["data_quality"]["rows_with_missing_values_dropped"] == 2
    assert result["data_quality"]["rows_analyzed"] == 1
    assert [q["qubit"] for q in result["qubits"]] == [0]


def test_status_boundary_is_inclusive_at_average():
    # Qubits with QSFI 10, 20, 30 -> average is 20.
    # Per spec, QSFI >= average is Stable, so the qubit exactly at the
    # average must be Stable, not Degrading.
    df = pd.DataFrame(
        {
            "Qubit": [0, 1, 2],
            "T1": [10.0, 20.0, 30.0],
            "T2": [10.0, 20.0, 30.0],
        }
    )

    result = analyze_qubit_data(df)
    status_by_qubit = {q["qubit"]: q["status"] for q in result["qubits"]}

    assert result["summary"]["average_qsfi"] == pytest.approx(20.0)
    assert status_by_qubit[0] == "Degrading"
    assert status_by_qubit[1] == "Stable"
    assert status_by_qubit[2] == "Stable"


def test_best_and_worst_qubit_are_identified_correctly():
    df = pd.DataFrame(
        {
            "Qubit": [5, 6, 7],
            "T1": [100.0, 10.0, 50.0],
            "T2": [100.0, 10.0, 50.0],
        }
    )

    result = analyze_qubit_data(df)
    best_qubit = result["summary"]["best_qubit"]
    worst_qubit = result["summary"]["worst_qubit"]

    assert best_qubit == {"qubit": 5, "qsfi": 100.0}
    assert worst_qubit == {"qubit": 6, "qsfi": 10.0}
    # `5.0 == 5` is True in Python, so also assert the type explicitly -
    # qubit ids must stay ints, not be silently upcast to float.
    assert isinstance(best_qubit["qubit"], int)
    assert isinstance(worst_qubit["qubit"], int)


def test_all_rows_invalid_raises_value_error():
    df = pd.DataFrame({"Qubit": [0, 1], "T1": [np.nan, np.nan], "T2": [1.0, 2.0]})

    with pytest.raises(ValueError, match="No valid rows"):
        analyze_qubit_data(df)


def test_qsfi_formula_is_exact_midpoint():
    df = pd.DataFrame({"Qubit": [0], "T1": [4.0], "T2": [10.0]})

    result = analyze_qubit_data(df)

    assert result["qubits"][0]["qsfi"] == pytest.approx(7.0)
