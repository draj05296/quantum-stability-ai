"""
Persists and retrieves saved analysis results using PostgreSQL.

Every successful /analyze call is stored as its own database record, so
/history and /compare/latest work across Render deployments and restarts.
"""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import psycopg


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not configured.")


def _get_connection():
    return psycopg.connect(DATABASE_URL)


def _ensure_table() -> None:
    """
    Creates the analysis history table if it does not already exist.
    """
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id BIGSERIAL PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    source_filename TEXT NOT NULL,
                    analyzed_at TIMESTAMPTZ NOT NULL,
                    analysis JSONB NOT NULL
                )
                """
            )
        conn.commit()


def save_analysis_result(source_filename: str, analysis: dict) -> dict:
    """
    Saves an analyzer result as a new PostgreSQL record.

    Every successful analysis receives a unique filename so previous
    analyses are never overwritten.
    """
    _ensure_table()

    analyzed_at = datetime.now(timezone.utc).isoformat()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]

    processed_filename = (
        f"{timestamp}_{unique_id}_{source_filename.rsplit('.', 1)[0]}.json"
    )

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analysis_history
                    (filename, source_filename, analyzed_at, analysis)
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    processed_filename,
                    source_filename,
                    analyzed_at,
                    json.dumps(analysis),
                ),
            )
        conn.commit()

    return {
        "filename": processed_filename,
        "analyzed_at": analyzed_at,
    }


def list_analyses() -> list[dict]:
    """
    Lists every saved analysis, newest first.
    """
    _ensure_table()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT filename, analyzed_at
                FROM analysis_history
                ORDER BY analyzed_at DESC
                """
            )

            rows = cur.fetchall()

    return [
        {
            "filename": row[0],
            "analyzed_at": row[1].isoformat(),
        }
        for row in rows
    ]


def load_analysis(filename: str) -> dict:
    """
    Loads one saved analysis from PostgreSQL by filename.
    """
    _ensure_table()

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    filename,
                    source_filename,
                    analyzed_at,
                    analysis
                FROM analysis_history
                WHERE filename = %s
                """,
                (filename,),
            )

            row = cur.fetchone()

    if row is None:
        raise FileNotFoundError(
            f"No saved analysis named {filename!r}."
        )

    record = {
        "analyzed_at": row[2].isoformat(),
        "source_filename": row[1],
        **row[3],
    }

    return record


def get_two_most_recent_analyses() -> tuple[dict, dict]:
    """
    Returns (previous, latest) full analysis records.

    Raises ValueError if fewer than two analyses exist.
    """
    entries = list_analyses()

    if len(entries) < 2:
        raise ValueError(
            f"At least two saved analyses are required to compare; "
            f"found {len(entries)}."
        )

    latest_entry = entries[0]
    previous_entry = entries[1]

    previous = load_analysis(previous_entry["filename"])
    latest = load_analysis(latest_entry["filename"])

    return previous, latest
