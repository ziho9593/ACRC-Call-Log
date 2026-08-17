from __future__ import annotations

import pytest

from app.config import get_settings


def test_diarization_rejects_mock_stt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "mock")
    monkeypatch.setenv("DIARIZATION_PROVIDER", "pyannote")

    with pytest.raises(ValueError, match="STT_PROVIDER=faster-whisper"):
        get_settings()
