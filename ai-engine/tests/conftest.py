"""
Shared pytest fixtures.

The services read `settings.UPLOAD_DIR` / `settings.PROCESSED_DIR` at call
time (not import time), so redirecting them on the settings object is enough
to keep every test writing into its own tmp_path instead of the real
`uploads/` and `processed/` folders.
"""

from types import SimpleNamespace

import pytest

from utils.config import settings


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
