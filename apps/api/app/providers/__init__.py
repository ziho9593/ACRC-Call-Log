from __future__ import annotations

from functools import cache
from pathlib import Path

from .base import CallAnalysisProvider, SpeechToTextProvider
from .faster_whisper import FasterWhisperSpeechToTextProvider
from .local_analysis import LocalExtractiveCallAnalysisProvider
from .mock import MockCallAnalysisProvider, MockSpeechToTextProvider
from .ollama_analysis import OllamaCallAnalysisProvider


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


@cache
def get_analysis_provider(
    name: str,
    base_url: str = "http://127.0.0.1:11434",
    model: str = "qwen3.5:4b",
    timeout_seconds: float = 180,
    context_window: int = 32768,
    max_input_chars: int = 40000,
) -> CallAnalysisProvider:
    if name == "mock":
        return MockCallAnalysisProvider()
    if name == "local":
        return LocalExtractiveCallAnalysisProvider()
    if name == "ollama":
        return OllamaCallAnalysisProvider(
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
            context_window=context_window,
            max_input_chars=max_input_chars,
        )
    raise ValueError(f"지원하지 않는 ANALYSIS_PROVIDER입니다: {name}")
