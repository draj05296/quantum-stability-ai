"""
API-level tests for the FastAPI routes in main.py.

These go through the real request/response cycle (routing, multipart parsing,
response-model validation, and the HTTPException -> status-code mapping), which
the service-level tests can't reach. Every test uses the `temp_dirs` fixture,
so uploads and saved analyses land in tmp_path rather than the real folders.
"""

import json

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.helpers import DAY1_CSV, DAY3_CSV, make_saved_record
from utils.config import settings

VALID_CSV = b"Qubit,T1,T2\n0,10.0,10.0\n1,30.0,30.0\n"


@pytest.fixture
def client(temp_dirs):
    """A TestClient bound to the throwaway upload/processed directories."""
    with TestClient(app) as test_client:
        yield test_client


def csv_upload(content=VALID_CSV, filename="data.csv"):
    return {"file": (filename, content, "text/csv")}


def save_processed(processed_dir, name, qsfi, timestamp, status="Stable"):
    record = make_saved_record([(0, qsfi, status)], source_filename=f"{name}.csv", analyzed_at=timestamp)
    (processed_dir / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


def test_health_reports_running(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "running"}


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------


def test_upload_saves_the_file_and_reports_its_shape(client, temp_dirs):
    response = client.post("/upload", files=csv_upload())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["rows"] == 2
    assert body["columns"] == ["Qubit", "T1", "T2"]
    assert (temp_dirs.uploads / body["filename"]).is_file()


def test_upload_filename_is_unique_per_request(client):
    first = client.post("/upload", files=csv_upload()).json()["filename"]
    second = client.post("/upload", files=csv_upload()).json()["filename"]

    assert first != second


def test_upload_rejects_non_csv_extensions(client, temp_dirs):
    response = client.post("/upload", files=csv_upload(filename="data.txt"))

    assert response.status_code == 400
    assert "Only .csv" in response.json()["detail"]
    # A rejected upload must not leave anything on disk.
    assert list(temp_dirs.uploads.iterdir()) == []


def test_upload_rejects_an_empty_file(client):
    response = client.post("/upload", files=csv_upload(content=b""))

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_rejects_files_over_the_size_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 16)

    response = client.post("/upload", files=csv_upload())

    assert response.status_code == 400
    assert "maximum allowed size" in response.json()["detail"]


def test_upload_without_the_file_field_is_422(client):
    response = client.post("/upload")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /analyze
# ---------------------------------------------------------------------------


def test_analyze_returns_summary_quality_and_per_qubit_results(client, temp_dirs):
    response = client.post("/analyze", files=csv_upload())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["summary"]["total_qubits"] == 2
    assert body["summary"]["average_qsfi"] == pytest.approx(20.0)
    assert body["data_quality"]["rows_analyzed"] == 2
    assert [q["qubit"] for q in body["qubits"]] == [0, 1]
    assert [q["status"] for q in body["qubits"]] == ["Degrading", "Stable"]


def test_analyze_persists_the_result_under_processed(client, temp_dirs):
    body = client.post("/analyze", files=csv_upload()).json()

    saved_path = temp_dirs.processed / body["processed_filename"]
    assert saved_path.is_file()

    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved["source_filename"] == body["filename"]
    assert saved["analyzed_at"] == body["analyzed_at"]
    assert saved["qubits"] == body["qubits"]


def test_analyze_on_the_real_day1_csv(client):
    with DAY1_CSV.open("rb") as f:
        response = client.post("/analyze", files={"file": ("day1.csv", f.read(), "text/csv")})

    assert response.status_code == 200
    body = response.json()
    # day1.csv has 156 rows, one of which is missing a T2 value.
    assert body["data_quality"]["rows_received"] == 156
    assert body["data_quality"]["rows_analyzed"] == 155
    assert len(body["qubits"]) == 155


def test_analyze_rejects_a_csv_missing_required_columns(client):
    response = client.post("/analyze", files=csv_upload(content=b"Qubit,T1\n0,10.0\n"))

    assert response.status_code == 400
    assert "T2" in response.json()["detail"]


def test_analyze_rejects_a_csv_with_no_usable_rows(client):
    response = client.post("/analyze", files=csv_upload(content=b"Qubit,T1,T2\n0,,10.0\n"))

    assert response.status_code == 400
    assert "No valid rows" in response.json()["detail"]


def test_analyze_reuses_the_upload_validation(client):
    """Bad uploads must fail the same way on /analyze as on /upload."""
    response = client.post("/analyze", files=csv_upload(filename="data.json"))

    assert response.status_code == 400
    assert "Only .csv" in response.json()["detail"]


def test_analyze_without_the_file_field_is_422(client):
    assert client.post("/analyze").status_code == 422


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------


def test_history_is_empty_before_anything_is_analyzed(client):
    response = client.get("/history")

    assert response.status_code == 200
    assert response.json() == {"count": 0, "analyses": []}


def test_history_lists_each_analysis_newest_first(client, temp_dirs):
    save_processed(temp_dirs.processed, "old", 10.0, "2026-01-01T00:00:00+00:00")
    save_processed(temp_dirs.processed, "new", 20.0, "2026-02-01T00:00:00+00:00")

    body = client.get("/history").json()

    assert body["count"] == 2
    assert [entry["filename"] for entry in body["analyses"]] == ["new.json", "old.json"]


def test_history_reflects_an_analyze_call(client):
    analyzed = client.post("/analyze", files=csv_upload()).json()

    body = client.get("/history").json()

    assert body["count"] == 1
    assert body["analyses"][0]["filename"] == analyzed["processed_filename"]
    assert body["analyses"][0]["analyzed_at"] == analyzed["analyzed_at"]


# ---------------------------------------------------------------------------
# GET /compare/latest
# ---------------------------------------------------------------------------


def test_compare_requires_two_analyses(client):
    response = client.get("/compare/latest")

    assert response.status_code == 400
    assert "At least two saved analyses" in response.json()["detail"]


def test_compare_with_only_one_analysis_is_still_400(client):
    client.post("/analyze", files=csv_upload())

    assert client.get("/compare/latest").status_code == 400


def test_compare_reports_changes_between_the_two_newest(client, temp_dirs):
    save_processed(temp_dirs.processed, "day1", 10.0, "2026-01-01T00:00:00+00:00", "Degrading")
    save_processed(temp_dirs.processed, "day2", 15.0, "2026-01-02T00:00:00+00:00", "Stable")

    response = client.get("/compare/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["previous"]["filename"] == "day1.csv"
    assert body["latest"]["filename"] == "day2.csv"
    assert body["qubits_compared"] == 1
    assert body["improved_qubits"] == [
        {"qubit": 0, "previous_qsfi": 10.0, "latest_qsfi": 15.0, "difference": pytest.approx(5.0)}
    ]
    assert body["degraded_qubits"] == []
    assert [q["qubit"] for q in body["newly_stable_qubits"]] == [0]
    assert body["newly_unstable_qubits"] == []


def test_compare_after_analyzing_day1_then_day3(client):
    """Full pipeline: two /analyze calls, then /compare/latest over the saved results."""
    for path in (DAY1_CSV, DAY3_CSV):
        with path.open("rb") as f:
            assert client.post("/analyze", files={"file": (path.name, f.read(), "text/csv")}).status_code == 200

    body = client.get("/compare/latest").json()

    assert body["qubits_compared"] == 155
    # Day 1 and Day 3 differ on every qubit, so every compared qubit lands in
    # exactly one of the two buckets.
    assert len(body["improved_qubits"]) + len(body["degraded_qubits"]) == 155
    assert body["average_qsfi_change"]["difference"] < 0
    assert body["latest"]["filename"].endswith("quantum_data_day3.csv")
    assert body["previous"]["filename"].endswith("quantum_data_day1.csv")
