from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    stt_provider: str
    analysis_provider: str
    database_path: Path
    upload_dir: Path
    processed_dir: Path
    max_upload_bytes: int
    cors_origins: list[str]


def get_settings() -> Settings:
    origins = os.getenv("API_CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        stt_provider=os.getenv("STT_PROVIDER", "mock"),
        analysis_provider=os.getenv("ANALYSIS_PROVIDER", "mock"),
        database_path=Path(os.getenv("DATABASE_PATH", "storage/acrc_call_log.db")),
        upload_dir=Path(os.getenv("UPLOAD_DIR", "storage/uploads")),
        processed_dir=Path(os.getenv("PROCESSED_DIR", "storage/processed")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))),
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )
