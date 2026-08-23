from __future__ import annotations

from pathlib import Path

import pytest

from app.config import PROJECT_ROOT, get_settings


def test_relative_storage_paths_are_resolved_from_project_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_PATH", "storage/test.db")
    monkeypatch.setenv("UPLOAD_DIR", "storage/test-uploads")
    monkeypatch.setenv("PROCESSED_DIR", "storage/test-processed")

    settings = get_settings()

    assert settings.database_path == PROJECT_ROOT / "storage/test.db"
    assert settings.upload_dir == PROJECT_ROOT / "storage/test-uploads"
    assert settings.processed_dir == PROJECT_ROOT / "storage/test-processed"


def test_diarization_rejects_mock_stt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "mock")
    monkeypatch.setenv("DIARIZATION_PROVIDER", "pyannote")

    with pytest.raises(ValueError, match="STT_PROVIDER=faster-whisper"):
        get_settings()
