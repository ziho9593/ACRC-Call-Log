from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.providers.base import SpeakerTurn, TranscriptResult, TranscriptUtterance
from app.providers.pyannote_diarization import (
    PyannoteSpeakerDiarizationProvider,
    assign_speakers,
)


class FakePipeline:
    device: Any = None
    call: tuple[object, dict[str, int]] | None = None

    def to(self, device: Any) -> None:
        type(self).device = device

    def __call__(self, audio: object, **options: int) -> object:
        type(self).call = (audio, options)
        annotation = [
            (SimpleNamespace(start=0.0, end=1.5), "SPEAKER_00"),
            (SimpleNamespace(start=1.5, end=3.0), "SPEAKER_01"),
        ]
        return SimpleNamespace(exclusive_speaker_diarization=annotation)


def test_pyannote_provider_converts_exclusive_diarization(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.yaml").write_text("pipeline: fake", encoding="utf-8")
    pipeline = FakePipeline()
    loaded_audio = {"waveform": "samples", "sample_rate": 16000}
    provider = PyannoteSpeakerDiarizationProvider(
        model_path=model_dir,
        device="cpu",
        min_speakers=2,
        max_speakers=3,
        pipeline_factory=lambda _: pipeline,
        audio_loader=lambda _: loaded_audio,
    )

    turns = provider.diarize("sample.wav")

    assert FakePipeline.device == "cpu"
    assert FakePipeline.call == (loaded_audio, {"min_speakers": 2, "max_speakers": 3})
    assert turns == [
        SpeakerTurn(0, 1500, "SPEAKER_00"),
        SpeakerTurn(1500, 3000, "SPEAKER_01"),
    ]


def test_assign_speakers_uses_greatest_overlap_and_stable_korean_labels() -> None:
    transcript = TranscriptResult(
        duration_ms=4000,
        utterances=[
            TranscriptUtterance(1, "화자", 100, 1200, "안녕하세요."),
            TranscriptUtterance(2, "화자", 1300, 2600, "문의드릴 게 있습니다."),
            TranscriptUtterance(3, "화자", 3100, 3500, "네."),
        ],
    )
    turns = [
        SpeakerTurn(0, 1500, "SPEAKER_07"),
        SpeakerTurn(1500, 3000, "SPEAKER_02"),
    ]

    result = assign_speakers(transcript, turns)

    assert [item.speaker for item in result.utterances] == ["화자 1", "화자 2", "화자 2"]
    assert [item.text for item in result.utterances] == [
        "안녕하세요.",
        "문의드릴 게 있습니다.",
        "네.",
    ]


def test_missing_model_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="화자분리 모델 디렉터리"):
        PyannoteSpeakerDiarizationProvider(
            model_path=tmp_path / "missing",
            pipeline_factory=lambda _: FakePipeline(),
        )
