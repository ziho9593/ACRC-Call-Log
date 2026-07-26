from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import get_settings
from .providers.base import AnalysisResult, TranscriptResult


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_db() -> None:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS call_records (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                duration_ms INTEGER,
                one_line_summary TEXT,
                detailed_summary TEXT,
                keywords TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS utterances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_record_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                speaker TEXT NOT NULL,
                start_ms INTEGER NOT NULL,
                end_ms INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (call_record_id) REFERENCES call_records(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS call_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_record_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_ms INTEGER NOT NULL,
                end_ms INTEGER NOT NULL,
                summary TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY (call_record_id) REFERENCES call_records(id) ON DELETE CASCADE
            );
            """
        )


@contextmanager
def connect() -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(get_settings().database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_call_record(
    *,
    call_id: str,
    original_filename: str,
    storage_path: Path,
    mime_type: str,
    file_size_bytes: int,
) -> sqlite3.Row:
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO call_records (
                id, original_filename, storage_path, mime_type, file_size_bytes,
                status, keywords, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'UPLOADED', '[]', ?, ?)
            """,
            (
                call_id,
                original_filename,
                str(storage_path),
                mime_type,
                file_size_bytes,
                now,
                now,
            ),
        )
        return get_call_record(call_id, conn=conn)


def list_call_records() -> list[sqlite3.Row]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM call_records ORDER BY created_at DESC LIMIT 30"
        ).fetchall()
    return list(rows)


def get_call_record(call_id: str, conn: sqlite3.Connection | None = None) -> sqlite3.Row | None:
    owns_conn = conn is None
    if conn is None:
        conn = sqlite3.connect(get_settings().database_path)
        conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM call_records WHERE id = ?", (call_id,)).fetchone()
    finally:
        if owns_conn:
            conn.close()


def get_utterances(call_id: str) -> list[sqlite3.Row]:
    with connect() as conn:
        return list(
            conn.execute(
                "SELECT * FROM utterances WHERE call_record_id = ? ORDER BY sequence",
                (call_id,),
            ).fetchall()
        )


def get_sections(call_id: str) -> list[sqlite3.Row]:
    with connect() as conn:
        return list(
            conn.execute(
                "SELECT * FROM call_sections WHERE call_record_id = ? ORDER BY sequence",
                (call_id,),
            ).fetchall()
        )


def update_status(call_id: str, status: str, error_message: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE call_records
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, error_message, utc_now(), call_id),
        )


def save_analysis(call_id: str, transcript: TranscriptResult, analysis: AnalysisResult) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM utterances WHERE call_record_id = ?", (call_id,))
        conn.execute("DELETE FROM call_sections WHERE call_record_id = ?", (call_id,))
        conn.executemany(
            """
            INSERT INTO utterances (
                call_record_id, sequence, speaker, start_ms, end_ms, text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (call_id, item.sequence, item.speaker, item.start_ms, item.end_ms, item.text)
                for item in transcript.utterances
            ],
        )
        conn.executemany(
            """
            INSERT INTO call_sections (
                call_record_id, sequence, title, start_ms, end_ms, summary, keywords
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    call_id,
                    item.sequence,
                    item.title,
                    item.start_ms,
                    item.end_ms,
                    item.summary,
                    json.dumps(item.keywords, ensure_ascii=False),
                )
                for item in analysis.sections
            ],
        )
        conn.execute(
            """
            UPDATE call_records
            SET status = 'COMPLETED',
                error_message = NULL,
                duration_ms = ?,
                one_line_summary = ?,
                detailed_summary = ?,
                keywords = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                transcript.duration_ms,
                analysis.one_line_summary,
                analysis.detailed_summary,
                json.dumps(analysis.keywords, ensure_ascii=False),
                utc_now(),
                call_id,
            ),
        )


def delete_call_record(call_id: str) -> sqlite3.Row | None:
    with connect() as conn:
        row = get_call_record(call_id, conn=conn)
        if row is None:
            return None
        conn.execute("DELETE FROM call_records WHERE id = ?", (call_id,))
        return row


def row_to_call_summary(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "originalFilename": row["original_filename"],
        "mimeType": row["mime_type"],
        "fileSizeBytes": row["file_size_bytes"],
        "status": row["status"],
        "errorMessage": row["error_message"],
        "durationMs": row["duration_ms"],
        "oneLineSummary": row["one_line_summary"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_to_call_detail(row: sqlite3.Row) -> dict[str, Any]:
    summary = row_to_call_summary(row)
    summary.update(
        {
            "detailedSummary": row["detailed_summary"],
            "keywords": json.loads(row["keywords"] or "[]"),
            "utterances": [
                {
                    "id": item["id"],
                    "sequence": item["sequence"],
                    "speaker": item["speaker"],
                    "startMs": item["start_ms"],
                    "endMs": item["end_ms"],
                    "text": item["text"],
                }
                for item in get_utterances(row["id"])
            ],
            "sections": [
                {
                    "id": item["id"],
                    "sequence": item["sequence"],
                    "title": item["title"],
                    "startMs": item["start_ms"],
                    "endMs": item["end_ms"],
                    "summary": item["summary"],
                    "keywords": json.loads(item["keywords"] or "[]"),
                }
                for item in get_sections(row["id"])
            ],
        }
    )
    return summary
