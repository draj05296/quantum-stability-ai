"""
Unit tests for services.history_service.

Every test runs against a throwaway `processed/` directory (the `temp_dirs`
fixture) so the real one is never read from or written to.
"""

import json

import pytest

from services.history_service import (
    get_two_most_recent_analyses,
    list_analyses,
    load_analysis,
    save_analysis_result,
)
from tests.helpers import make_analysis, make_saved_record


def write_record(processed_dir, filename, analyzed_at, source_filename="source.csv"):
    """Writes a saved-analysis JSON file directly, with a controlled timestamp."""
    record = make_saved_record(
        [(0, 1.0, "Stable")], source_filename=source_filename, analyzed_at=analyzed_at
    )
    (processed_dir / filename).write_text(json.dumps(record), encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# save_analysis_result
# ---------------------------------------------------------------------------


def test_save_writes_json_named_after_the_source_csv(temp_dirs):
    analysis = make_analysis([(0, 1.0, "Stable"), (1, 3.0, "Stable")])

    saved = save_analysis_result("20260805_143022_a1b2c3d4_day1.csv", analysis)

    assert saved["filename"] == "20260805_143022_a1b2c3d4_day1.json"
    assert (temp_dirs.processed / saved["filename"]).is_file()


def test_saved_record_keeps_the_analysis_plus_provenance(temp_dirs):
    analysis = make_analysis([(7, 2.0, "Stable")])

    saved = save_analysis_result("day1.csv", analysis)
    written = json.loads((temp_dirs.processed / saved["filename"]).read_text(encoding="utf-8"))

    # The analyzer's own output must survive untouched...
    assert written["summary"] == analysis["summary"]
    assert written["qubits"] == analysis["qubits"]
    assert written["data_quality"] == analysis["data_quality"]
    # ...alongside the provenance /history and /compare/latest depend on.
    assert written["source_filename"] == "day1.csv"
    assert written["analyzed_at"] == saved["analyzed_at"]


def test_saving_a_second_analysis_does_not_replace_the_first(temp_dirs):
    """The core 'keep history instead of overwriting' guarantee."""
    first = save_analysis_result("day1.csv", make_analysis([(0, 1.0, "Stable")]))
    second = save_analysis_result("day2.csv", make_analysis([(0, 2.0, "Stable")]))

    assert first["filename"] != second["filename"]
    assert (temp_dirs.processed / first["filename"]).is_file()
    assert (temp_dirs.processed / second["filename"]).is_file()
    assert len(list(temp_dirs.processed.glob("*.json"))) == 2


def test_save_creates_the_processed_directory_when_missing(tmp_path, monkeypatch):
    from utils.config import settings

    missing_dir = tmp_path / "not-created-yet"
    monkeypatch.setattr(settings, "PROCESSED_DIR", str(missing_dir))

    saved = save_analysis_result("day1.csv", make_analysis([(0, 1.0, "Stable")]))

    assert (missing_dir / saved["filename"]).is_file()


# ---------------------------------------------------------------------------
# list_analyses
# ---------------------------------------------------------------------------


def test_list_is_empty_when_nothing_has_been_saved(temp_dirs):
    assert list_analyses() == []


def test_list_returns_newest_first(temp_dirs):
    # Written oldest-first on purpose; ordering must come from analyzed_at,
    # not from filesystem/glob order.
    write_record(temp_dirs.processed, "a.json", "2026-01-01T00:00:00+00:00")
    write_record(temp_dirs.processed, "b.json", "2026-03-01T00:00:00+00:00")
    write_record(temp_dirs.processed, "c.json", "2026-02-01T00:00:00+00:00")

    entries = list_analyses()

    assert [entry["filename"] for entry in entries] == ["b.json", "c.json", "a.json"]
    assert [entry["analyzed_at"] for entry in entries] == [
        "2026-03-01T00:00:00+00:00",
        "2026-02-01T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    ]


def test_list_entries_expose_only_filename_and_timestamp(temp_dirs):
    save_analysis_result("day1.csv", make_analysis([(0, 1.0, "Stable")]))

    assert set(list_analyses()[0]) == {"filename", "analyzed_at"}


def test_list_ignores_non_json_files(temp_dirs):
    write_record(temp_dirs.processed, "real.json", "2026-01-01T00:00:00+00:00")
    (temp_dirs.processed / "notes.txt").write_text("ignore me", encoding="utf-8")

    assert [entry["filename"] for entry in list_analyses()] == ["real.json"]


# ---------------------------------------------------------------------------
# load_analysis
# ---------------------------------------------------------------------------


def test_save_then_load_round_trips_the_full_record(temp_dirs):
    analysis = make_analysis([(3, 5.0, "Stable"), (4, 1.0, "Degrading")])
    saved = save_analysis_result("day1.csv", analysis)

    loaded = load_analysis(saved["filename"])

    assert loaded["qubits"] == analysis["qubits"]
    assert loaded["summary"]["average_qsfi"] == analysis["summary"]["average_qsfi"]
    assert loaded["source_filename"] == "day1.csv"


def test_load_unknown_filename_raises_file_not_found(temp_dirs):
    with pytest.raises(FileNotFoundError, match="nope.json"):
        load_analysis("nope.json")


@pytest.mark.parametrize(
    "filename",
    ["../secrets.json", "../../etc/passwd", "sub/../../escape.json"],
)
def test_load_rejects_paths_that_escape_the_processed_directory(temp_dirs, filename):
    with pytest.raises(ValueError, match="Invalid filename"):
        load_analysis(filename)


# ---------------------------------------------------------------------------
# get_two_most_recent_analyses
# ---------------------------------------------------------------------------


def test_returns_previous_then_latest_in_chronological_order(temp_dirs):
    write_record(temp_dirs.processed, "older.json", "2026-01-01T00:00:00+00:00", "day1.csv")
    write_record(temp_dirs.processed, "newer.json", "2026-02-01T00:00:00+00:00", "day2.csv")

    previous, latest = get_two_most_recent_analyses()

    assert previous["source_filename"] == "day1.csv"
    assert latest["source_filename"] == "day2.csv"


def test_only_the_two_newest_are_returned(temp_dirs):
    write_record(temp_dirs.processed, "oldest.json", "2026-01-01T00:00:00+00:00", "day1.csv")
    write_record(temp_dirs.processed, "middle.json", "2026-02-01T00:00:00+00:00", "day2.csv")
    write_record(temp_dirs.processed, "newest.json", "2026-03-01T00:00:00+00:00", "day3.csv")

    previous, latest = get_two_most_recent_analyses()

    assert previous["source_filename"] == "day2.csv"
    assert latest["source_filename"] == "day3.csv"


@pytest.mark.parametrize("saved_count", [0, 1])
def test_fewer_than_two_analyses_raises_value_error(temp_dirs, saved_count):
    for index in range(saved_count):
        write_record(temp_dirs.processed, f"{index}.json", f"2026-01-0{index + 1}T00:00:00+00:00")

    with pytest.raises(ValueError, match=f"found {saved_count}"):
        get_two_most_recent_analyses()
