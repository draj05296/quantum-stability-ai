"""Business logic for handling CSV uploads: validate, save, then inspect with pandas."""

import os

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from utils.config import settings
from utils.file_utils import generate_unique_filename

# Bytes pulled from the upload stream per iteration: small enough that an
# oversized upload is caught promptly, large enough to keep the loop cheap.
UPLOAD_CHUNK_SIZE = 64 * 1024


async def save_and_inspect_csv(file: UploadFile) -> dict:
    """
    Validates an uploaded CSV, saves it to `settings.UPLOAD_DIR` under a
    unique filename, and reads it with pandas to report its shape. Backs
    the /upload endpoint.
    """
    filename, dataframe = await save_and_load_csv(file)

    return {
        "success": True,
        "filename": filename,
        "rows": int(dataframe.shape[0]),
        "columns": dataframe.columns.tolist(),
    }


async def save_and_load_csv(file: UploadFile) -> tuple[str, pd.DataFrame]:
    """
    Validates an uploaded CSV, saves it to `settings.UPLOAD_DIR` under a
    unique filename, and loads it into a DataFrame.

    This is the shared validate -> save -> parse step used by any endpoint
    that needs both the file on disk and its parsed contents (currently
    /upload and /analyze), so that logic only lives in one place.

    Raises HTTPException(400) for anything wrong with the upload itself
    (extension, size, unparseable content) and HTTPException(500) if saving
    to disk fails.
    """
    _validate_extension(file.filename)

    contents = await _read_within_size_limit(file)
    _validate_size(len(contents))

    filename = generate_unique_filename(file.filename)
    file_path = _save_file(filename, contents)
    dataframe = _read_csv(file_path)

    return filename, dataframe


async def _read_within_size_limit(file: UploadFile) -> bytes:
    """
    Reads the upload in chunks, stopping as soon as the accumulated size
    exceeds `settings.MAX_UPLOAD_SIZE_BYTES`.

    Previously the whole body was materialised with a single `await
    file.read()` and only measured afterwards, so an arbitrarily large upload
    was held in memory before being rejected. Reading incrementally caps what
    this process ever holds at roughly the configured limit.

    Note this bounds *our* memory, not the transfer: by the time the endpoint
    runs, Starlette has already received and spooled the request body (to a
    temporary file once it passes ~1 MB). Refusing the connection earlier
    than that needs a limit at the proxy/ASGI layer, which is a deployment
    concern rather than an application one.
    """
    chunks: list[bytes] = []
    total_bytes = 0

    while True:
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break

        total_bytes += len(chunk)
        if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_max_size_message(),
            )

        chunks.append(chunk)

    return b"".join(chunks)


def _read_csv(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception as exc:
        # Don't leave an unreadable file behind in uploads/.
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file could not be parsed as CSV: {exc}",
        ) from exc


def _validate_extension(filename: str | None) -> None:
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file was provided.")

    extension = os.path.splitext(filename)[1].lower()
    if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension or 'unknown'}'. Only {allowed} files are allowed.",
        )


def _max_size_message() -> str:
    """Shared so the streaming guard and the final check can't drift apart."""
    max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
    return f"File exceeds the maximum allowed size of {max_mb} MB."


def _validate_size(size_bytes: int) -> None:
    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # _read_within_size_limit already rejects oversized uploads while
    # streaming; this stays as a defensive backstop for any caller that
    # supplies bytes some other way.
    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_max_size_message(),
        )


def _save_file(filename: str, contents: bytes) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        ) from exc

    return file_path
