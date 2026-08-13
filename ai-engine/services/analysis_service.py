"""
Orchestrates the /analyze endpoint.

This module contains no upload-handling or analysis logic itself - it only
wires services.upload_service (validate/save/load), services.analyzer (the
computation), and services.history_service (persisting the result) together,
so none of them has to know about the others.
"""

from fastapi import HTTPException, UploadFile, status

from services.analyzer import analyze_qubit_data
from services.history_service import save_analysis_result
from services.upload_service import save_and_load_csv


async def analyze_uploaded_csv(file: UploadFile) -> dict:
    """
    Validates and saves the uploaded CSV (reusing services.upload_service),
    runs services.analyzer on the parsed DataFrame, then persists the result
    under processed/ (via services.history_service) so it's available to
    /history and /compare/latest without recomputing anything.

    Raises HTTPException(400) if the upload itself is invalid (propagated
    from save_and_load_csv) or if the analyzer rejects the data (missing
    required columns, no valid rows left after cleaning) - both are
    problems with the client's input, not the server.
    """
    filename, dataframe = await save_and_load_csv(file)

    try:
        analysis = analyze_qubit_data(dataframe)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    saved = save_analysis_result(filename, analysis)

    return {
        "success": True,
        "filename": filename,
        "processed_filename": saved["filename"],
        "analyzed_at": saved["analyzed_at"],
        **analysis,
    }
