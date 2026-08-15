from __future__ import annotations

from functools import cache
from pathlib import Path

from .base import CallAnalysisProvider, SpeechToTextProvider
from .faster_whisper import FasterWhisperSpeechToTextProvider
from .mock import MockCallAnalysisProvider, MockSpeechToTextProvider


@cache
def get_stt_provider(
    name: str,
    model_path: Path | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "ko",
) -> SpeechToTextProvider:
    if name == "mock":
        return MockSpeechToTextProvider()
    if name == "faster-whisper":
        if model_path is None:
            raise ValueError("faster-whisper Provider에는 모델 경로가 필요합니다.")
        return FasterWhisperSpeechToTextProvider(
            model_path=model_path,
            device=device,
            compute_type=compute_type,
            language=language,
        )
    raise ValueError(f"지원하지 않는 STT_PROVIDER입니다: {name}")


def get_analysis_provider(name: str) -> CallAnalysisProvider:
    if name == "mock":
        return MockCallAnalysisProvider()
    raise ValueError(f"지원하지 않는 ANALYSIS_PROVIDER입니다: {name}")
