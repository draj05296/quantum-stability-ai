"""
Tests for the deployment-facing behaviour of the backend.

Covers the parts that only matter once the app runs somewhere other than a
developer's machine: environment-driven storage paths, CORS for both local and
production origins, the streaming upload-size guard, and - most importantly -
that none of it changes the scientific output.
"""

import asyncio
import json

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

import main
from services.analyzer import analyze_qubit_data
from services.compare_service import get_latest_comparison
from services.history_service import list_analyses, save_analysis_result
from fastapi import HTTPException
from services.upload_service import (
    UPLOAD_CHUNK_SIZE,
    _max_size_message,
    _read_within_size_limit,
)
from tests.helpers import DAY1_CSV, make_analysis, make_saved_record
from utils.config import Settings, settings

LOCAL_ORIGIN = "http://localhost:5173"
VITE_ALT_ORIGIN = "http://localhost:5174"
PRODUCTION_ORIGIN = "https://qsfi.example.app"
FOREIGN_ORIGIN = "https://not-our-frontend.example.com"


# ---------------------------------------------------------------------------
# Configurable storage paths (CHANGE 3)
# ---------------------------------------------------------------------------


def test_storage_paths_default_to_the_existing_local_folders():
    """The local project must keep working with no environment set."""
    defaults = Settings(_env_file=None)

    assert defaults.UPLOAD_DIR == "uploads"
    assert defaults.PROCESSED_DIR == "processed"


def test_storage_paths_are_overridable_by_environment(monkeypatch):
    monkeypatch.setenv("AI_ENGINE_UPLOAD_DIR", "/mnt/data/uploads")
    monkeypatch.setenv("AI_ENGINE_PROCESSED_DIR", "/mnt/data/processed")

    configured = Settings(_env_file=None)

    assert configured.UPLOAD_DIR == "/mnt/data/uploads"
    assert configured.PROCESSED_DIR == "/mnt/data/processed"


def test_upload_size_limit_is_overridable_by_environment(monkeypatch):
    monkeypatch.setenv("AI_ENGINE_MAX_UPLOAD_SIZE_BYTES", "2048")

    assert Settings(_env_file=None).MAX_UPLOAD_SIZE_BYTES == 2048


# ---------------------------------------------------------------------------
# History/compare against an absolute mounted path (CHANGE 6)
# ---------------------------------------------------------------------------


def test_history_and_compare_work_with_an_absolute_processed_dir(tmp_path, monkeypatch):
    """
    Simulates a mounted production disk: PROCESSED_DIR is an absolute path
    outside the project. Everything must behave exactly as with the relative
    default.
    """
    mounted = tmp_path / "mnt" / "data" / "processed"
    mounted.mkdir(parents=True)
    monkeypatch.setattr(settings, "PROCESSED_DIR", str(mounted))

    for name, qsfi, timestamp, status_label in [
        ("day1", 10.0, "2026-01-01T00:00:00+00:00", "Degrading"),
        ("day2", 15.0, "2026-01-02T00:00:00+00:00", "Stable"),
    ]:
        record = make_saved_record(
            [(0, qsfi, status_label)], source_filename=f"{name}.csv", analyzed_at=timestamp
        )
        (mounted / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")

    entries = list_analyses()
    assert [entry["filename"] for entry in entries] == ["day2.json", "day1.json"]

    comparison = get_latest_comparison()
    assert comparison["previous"]["filename"] == "day1.csv"
    assert comparison["latest"]["filename"] == "day2.csv"
    assert [q["qubit"] for q in comparison["improved_qubits"]] == [0]
    assert [q["qubit"] for q in comparison["newly_stable_qubits"]] == [0]


def test_saving_into_an_absolute_processed_dir_keeps_the_same_filenames(tmp_path, monkeypatch):
    """Analysis file naming must not change with the storage location."""
    mounted = tmp_path / "mnt" / "processed"
    monkeypatch.setattr(settings, "PROCESSED_DIR", str(mounted))

    saved = save_analysis_result(
        "20260805_143022_a1b2c3d4_day1.csv", make_analysis([(0, 1.0, "Stable")])
    )

    assert saved["filename"] == "20260805_143022_a1b2c3d4_day1.json"
    assert (mounted / saved["filename"]).is_file()


# ---------------------------------------------------------------------------
# Streaming upload-size guard (CHANGE 5)
# ---------------------------------------------------------------------------


class CountingUpload:
    """Minimal UploadFile stand-in that records how much was actually read."""

    def __init__(self, payload: bytes):
        self._payload = payload
        self._offset = 0
        self.bytes_read = 0

    async def read(self, size: int = -1) -> bytes:
        chunk = (
            self._payload[self._offset :]
            if size < 0
            else self._payload[self._offset : self._offset + size]
        )
        self._offset += len(chunk)
        self.bytes_read += len(chunk)
        return chunk


def test_oversized_upload_is_rejected_without_reading_it_all(monkeypatch):
    """The whole point of the change: stop reading once the limit is passed."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 128 * 1024)
    upload = CountingUpload(b"x" * (5 * 1024 * 1024))  # 5 MB against a 128 KB cap

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_read_within_size_limit(upload))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == _max_size_message()
    # Reading stopped just past the limit rather than consuming all 5 MB.
    assert upload.bytes_read < 5 * 1024 * 1024
    assert upload.bytes_read <= settings.MAX_UPLOAD_SIZE_BYTES + UPLOAD_CHUNK_SIZE


def test_upload_within_the_limit_is_returned_intact():
    payload = b"Qubit,T1,T2\n0,1.0,2.0\n" * 100

    assert asyncio.run(_read_within_size_limit(CountingUpload(payload))) == payload


def test_oversized_upload_still_returns_the_same_400_over_http(temp_dirs, monkeypatch):
    """The HTTP contract must be unchanged by the streaming rewrite."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 1024)

    with TestClient(main.app) as client:
        response = client.post(
            "/analyze", files={"file": ("big.csv", b"x" * 4096, "text/csv")}
        )

    assert response.status_code == 400
    assert "maximum allowed size" in response.json()["detail"]


# ---------------------------------------------------------------------------
# CORS (CHANGE 4)
# ---------------------------------------------------------------------------


def allowed_origin_header(client, origin):
    response = client.options(
        "/analyze",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    return response.headers.get("access-control-allow-origin")


def test_cors_allows_the_local_vite_origins(temp_dirs):
    with TestClient(main.app) as client:
        assert allowed_origin_header(client, LOCAL_ORIGIN) == LOCAL_ORIGIN
        # Vite's auto-incremented port, matched by the regex.
        assert allowed_origin_header(client, VITE_ALT_ORIGIN) == VITE_ALT_ORIGIN


def test_cors_rejects_an_unknown_origin_by_default(temp_dirs):
    with TestClient(main.app) as client:
        assert allowed_origin_header(client, FOREIGN_ORIGIN) is None
        assert allowed_origin_header(client, PRODUCTION_ORIGIN) is None


def test_cors_never_uses_a_wildcard_origin(temp_dirs):
    """Credentials are enabled, so '*' would be both unsafe and non-functional."""
    with TestClient(main.app) as client:
        assert allowed_origin_header(client, FOREIGN_ORIGIN) != "*"
        assert "*" not in settings.ALLOWED_ORIGINS


def test_production_origin_is_configurable_by_environment(monkeypatch):
    """A hosting platform supplies the frontend origin as a JSON list."""
    monkeypatch.setenv("AI_ENGINE_ALLOWED_ORIGINS", f'["{PRODUCTION_ORIGIN}"]')

    assert Settings(_env_file=None).ALLOWED_ORIGINS == [PRODUCTION_ORIGIN]


def test_main_wires_cors_from_settings_rather_than_literals():
    """
    Guards the link between config and middleware: if main.py ever stopped
    sourcing CORS from settings, the environment override would silently do
    nothing in production.
    """
    cors_middleware = next(
        mw for mw in main.app.user_middleware if mw.cls is CORSMiddleware
    )

    assert cors_middleware.kwargs["allow_origins"] is settings.ALLOWED_ORIGINS
    assert cors_middleware.kwargs["allow_origin_regex"] is settings.ALLOWED_ORIGIN_REGEX
    assert cors_middleware.kwargs["allow_credentials"] is True


def test_configured_production_origin_is_admitted_by_the_middleware(monkeypatch):
    """
    Behavioural check: an app built with the production settings must accept
    the production origin and still reject an unrelated one.

    A fresh app is used rather than reloading main, because reloading would
    replace the module-level `settings` object that every other test holds a
    reference to. The middleware arguments mirror main.py, and the test above
    pins main.py to those same settings values.
    """
    monkeypatch.setenv("AI_ENGINE_ALLOWED_ORIGINS", f'["{PRODUCTION_ORIGIN}"]')
    production_settings = Settings(_env_file=None)

    production_app = FastAPI()
    production_app.add_middleware(
        CORSMiddleware,
        allow_origins=production_settings.ALLOWED_ORIGINS,
        allow_origin_regex=production_settings.ALLOWED_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @production_app.post("/analyze")
    def _analyze():
        return {"ok": True}

    with TestClient(production_app) as client:
        assert allowed_origin_header(client, PRODUCTION_ORIGIN) == PRODUCTION_ORIGIN
        assert allowed_origin_header(client, FOREIGN_ORIGIN) is None
        # Local development keeps working alongside the production origin.
        assert allowed_origin_header(client, LOCAL_ORIGIN) == LOCAL_ORIGIN


# ---------------------------------------------------------------------------
# Startup / runtime configuration (CHANGE 1)
# ---------------------------------------------------------------------------


def test_startup_creates_the_configured_storage_directories(tmp_path, monkeypatch):
    uploads = tmp_path / "created" / "uploads"
    processed = tmp_path / "created" / "processed"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(uploads))
    monkeypatch.setattr(settings, "PROCESSED_DIR", str(processed))

    assert not uploads.exists() and not processed.exists()

    with TestClient(main.app):
        pass

    assert uploads.is_dir()
    assert processed.is_dir()


def test_health_endpoint_still_reports_running(temp_dirs):
    with TestClient(main.app) as client:
        assert client.get("/health").json() == {"status": "running"}


# ---------------------------------------------------------------------------
# Scientific invariance - the whole point of the protected core
# ---------------------------------------------------------------------------


def test_day1_analysis_output_is_byte_for_byte_unchanged():
    """
    Pins the full analyzer result for the known day-1 CSV. Any hardening
    change that altered a QSFI value, a status, or the cleaning bookkeeping
    would fail here.
    """
    result = analyze_qubit_data(pd.read_csv(DAY1_CSV))
    summary = result["summary"]

    assert summary["total_qubits"] == 155
    assert summary["average_t1"] == pytest.approx(0.00014699268600843761)
    assert summary["average_t2"] == pytest.approx(0.00010441423661321995)
    assert summary["average_qsfi"] == pytest.approx(0.00012570346131082877)
    assert summary["best_qubit"]["qubit"] == 3
    assert summary["worst_qubit"]["qubit"] == 149

    assert result["data_quality"] == {
        "rows_received": 156,
        "duplicate_rows_removed": 0,
        "missing_values": {"Qubit": 0, "T1": 0, "T2": 1},
        "rows_with_missing_values_dropped": 1,
        "rows_analyzed": 155,
    }

    assert len(result["qubits"]) == 155
    assert sum(1 for q in result["qubits"] if q["status"] == "Stable") == 73
