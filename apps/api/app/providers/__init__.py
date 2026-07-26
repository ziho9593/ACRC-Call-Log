from __future__ import annotations

from .base import CallAnalysisProvider, SpeechToTextProvider
from .mock import MockCallAnalysisProvider, MockSpeechToTextProvider


def get_stt_provider(name: str) -> SpeechToTextProvider:
    if name == "mock":
        return MockSpeechToTextProvider()
    raise ValueError(f"지원하지 않는 STT_PROVIDER입니다: {name}")


def get_analysis_provider(name: str) -> CallAnalysisProvider:
    if name == "mock":
        return MockCallAnalysisProvider()
    raise ValueError(f"지원하지 않는 ANALYSIS_PROVIDER입니다: {name}")
