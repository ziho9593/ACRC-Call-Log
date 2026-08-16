from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.services import preprocess_audio_for_stt


def test_preprocess_audio_builds_normalized_wav(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.mp3"
    source.write_bytes(b"audio")
    captured_command: list[str] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        captured_command.extend(command)
        Path(command[-1]).write_bytes(b"wav")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = preprocess_audio_for_stt(source, tmp_path / "processed", "call-id")

    assert result == tmp_path / "processed" / "call-id-stt.wav"
    assert result.read_bytes() == b"wav"
    assert captured_command[:2] == ["ffmpeg", "-hide_banner"]
    assert captured_command[captured_command.index("-ac") + 1] == "1"
    assert captured_command[captured_command.index("-ar") + 1] == "16000"
    assert "afftdn" in captured_command[captured_command.index("-af") + 1]
    assert "loudnorm" in captured_command[captured_command.index("-af") + 1]


def test_preprocess_audio_removes_partial_output_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.mp3"
    source.write_bytes(b"audio")
    output = tmp_path / "processed" / "call-id-stt.wav"

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        Path(command[-1]).write_bytes(b"partial")
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        preprocess_audio_for_stt(source, output.parent, "call-id")

    assert not output.exists()
