from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.providers.faster_whisper import FasterWhisperSpeechToTextProvider


class FakeWhisperModel:
    init_options: dict[str, Any] = {}
    transcribe_options: dict[str, Any] = {}

    def __init__(self, model_path: str, **options: Any) -> None:
        self.init_options = {"model_path": model_path, **options}
        type(self).init_options = self.init_options

    def transcribe(self, audio_path: str, **options: Any) -> tuple[object, object]:
        self.transcribe_options = {"audio_path": audio_path, **options}
        type(self).transcribe_options = self.transcribe_options
        segments = iter(
            [
                SimpleNamespace(start=0.25, end=1.5, text=" 첫 번째 문장 "),
                SimpleNamespace(start=1.5, end=2.0, text="   "),
                SimpleNamespace(start=2.0, end=3.75, text="두 번째 문장"),
            ]
        )
        return segments, SimpleNamespace(duration=4.0)


def test_transcribe_converts_whisper_segments(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    provider = FasterWhisperSpeechToTextProvider(
        model_path=model_dir,
        device="cpu",
        compute_type="int8",
        language="ko",
        initial_prompt="민원 상담 통화",
        hotwords="민원, 접수번호",
        model_factory=FakeWhisperModel,
    )

    result = provider.transcribe("sample.mp3")

    assert FakeWhisperModel.init_options == {
        "model_path": str(model_dir),
        "device": "cpu",
        "compute_type": "int8",
        "local_files_only": True,
    }
    assert FakeWhisperModel.transcribe_options == {
        "audio_path": "sample.mp3",
        "language": "ko",
        "beam_size": 5,
        "vad_filter": True,
        "vad_parameters": {
            "threshold": 0.35,
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 400,
        },
        "initial_prompt": "민원 상담 통화",
        "hotwords": "민원, 접수번호",
        "condition_on_previous_text": False,
    }
    assert result.duration_ms == 4000
    assert [utterance.text for utterance in result.utterances] == [
        "첫 번째 문장",
        "두 번째 문장",
    ]
    assert [utterance.sequence for utterance in result.utterances] == [1, 2]
    assert all(utterance.speaker == "화자" for utterance in result.utterances)
    assert result.utterances[0].start_ms == 250
    assert result.utterances[1].end_ms == 3750


def test_missing_model_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Whisper 모델 디렉터리"):
        FasterWhisperSpeechToTextProvider(
            model_path=tmp_path / "missing",
            model_factory=FakeWhisperModel,
        )
