"""
Persists and retrieves saved analysis results under `processed/`.

Every successful /analyze call is written here as its own JSON file, so
later requests (like /history and /compare/latest) can be served by reading
those files back instead of re-uploading or re-analyzing anything.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from utils.config import settings
from utils.file_utils import resolve_safe_path


def save_analysis_result(source_filename: str, analysis: dict) -> dict:
    """
    Writes an analyzer result to `processed/` as its own timestamped JSON
    file (never overwriting a previous one) and returns
    `{"filename": ..., "analyzed_at": ...}` for that saved record.
    """
    analyzed_at = datetime.now(timezone.utc).isoformat()
    processed_filename = f"{Path(source_filename).stem}.json"

    record = {
        "analyzed_at": analyzed_at,
        "source_filename": source_filename,
        **analysis,
    }

    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    file_path = Path(settings.PROCESSED_DIR) / processed_filename
    file_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    return {"filename": processed_filename, "analyzed_at": analyzed_at}


def list_analyses() -> list[dict]:
    """
    Lists every saved analysis as `{"filename": ..., "analyzed_at": ...}`,
    newest first. Returns an empty list if none have been saved yet.
    """
    entries = []

    for file_path in Path(settings.PROCESSED_DIR).glob("*.json"):
        record = _read_json(file_path)
        entries.append({"filename": file_path.name, "analyzed_at": record.get("analyzed_at", "")})

    entries.sort(key=lambda entry: entry["analyzed_at"], reverse=True)
    return entries


def load_analysis(filename: str) -> dict:
    """Reads one saved analysis record by its processed/ filename."""
    file_path = resolve_safe_path(settings.PROCESSED_DIR, filename)

    if not file_path.is_file():
        raise FileNotFoundError(f"No saved analysis named {filename!r}.")

    return _read_json(file_path)


def get_two_most_recent_analyses() -> tuple[dict, dict]:
    """
    Returns the (previous, latest) full analysis records, newest last.
    Raises ValueError if fewer than two analyses have been saved.
    """
    entries = list_analyses()

    if len(entries) < 2:
        raise ValueError(
            f"At least two saved analyses are required to compare; found {len(entries)}."
        )

    latest_entry, previous_entry = entries[0], entries[1]
    return load_analysis(previous_entry["filename"]), load_analysis(latest_entry["filename"])


def _read_json(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)
