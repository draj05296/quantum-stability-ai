"""
Shared pytest fixtures.

The services read `settings.UPLOAD_DIR` / `settings.PROCESSED_DIR` at call
time (not import time), so redirecting them on the settings object is enough
to keep every test writing into its own tmp_path instead of the real
`uploads/` and `processed/` folders.
"""

import os
from types import SimpleNamespace

import pytest

# services.history_service reads DATABASE_URL at *import* time and raises
# RuntimeError if it's unset - which happens before any test or fixture runs,
# so it can't be handled with a fixture. A placeholder here only lets modules
# that depend on history_service be imported during collection; it is never
# meant to be connected to. Tests that need history_service's behavior
# without a real database monkeypatch its functions (or trend_service's/
# risk_service's imported references to them) directly - see
# test_trend_service.py.
#
# 127.0.0.1 with a closed low port + a short connect_timeout is deliberate:
# if some pre-existing test *does* still reach a real psycopg.connect() call
# (several do - they predate this Postgres migration and were not part of
# this task), it fails in ~3s with a clear connection error instead of
# hanging for the OS's full TCP timeout, which on this machine silently
# stalls for minutes against an unreachable standard Postgres port.
#
# A real DATABASE_URL in the environment always takes precedence.
os.environ.setdefault(
    "DATABASE_URL", "postgresql://unused:unused@127.0.0.1:1/unused?connect_timeout=3"
)

from utils.config import settings  # noqa: E402


@pytest.fixture
def temp_dirs(tmp_path, monkeypatch):
    """Points UPLOAD_DIR/PROCESSED_DIR at throwaway directories for one test."""
    uploads = tmp_path / "uploads"
    processed = tmp_path / "processed"
    uploads.mkdir()
    processed.mkdir()

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(uploads))
    monkeypatch.setattr(settings, "PROCESSED_DIR", str(processed))

    return SimpleNamespace(uploads=uploads, processed=processed)
