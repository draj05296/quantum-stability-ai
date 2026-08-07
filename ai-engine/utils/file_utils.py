"""Filesystem helpers shared by upload/processing endpoints."""

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SAFE_STEM_MAX_LENGTH = 50
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def generate_unique_filename(original_filename: str, extension: str = ".csv") -> str:
    """
    Builds a filesystem-safe, collision-resistant filename from a
    user-supplied original name: `<timestamp>_<random-id>_<sanitized-stem>.csv`.

    The original filename is never trusted as-is (it may contain path
    separators or unsafe characters) - only its sanitized stem is kept, and
    the extension is always the one this function is told to use, not
    whatever the client sent.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    # Path(...).stem also strips any directory components the client may
    # have sent (e.g. "../../etc/passwd"), so only the base name survives.
    raw_stem = Path(original_filename or "upload").stem
    safe_stem = _UNSAFE_CHARS.sub("-", raw_stem).strip("-")[:_SAFE_STEM_MAX_LENGTH]
    safe_stem = safe_stem or "upload"

    return f"{timestamp}_{unique_id}_{safe_stem}{extension}"
