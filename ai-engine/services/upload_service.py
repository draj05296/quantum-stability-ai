"""Business logic for handling CSV uploads: validate, save, then inspect with pandas."""

import os

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from utils.config import settings
from utils.file_utils import generate_unique_filename


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

    contents = await file.read()
    _validate_size(len(contents))

    filename = generate_unique_filename(file.filename)
    file_path = _save_file(filename, contents)
    dataframe = _read_csv(file_path)

    return filename, dataframe


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


def _validate_size(size_bytes: int) -> None:
    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the maximum allowed size of {max_mb} MB.",
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
