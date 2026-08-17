from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptUtterance:
    sequence: int
    speaker: str
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    duration_ms: int
    utterances: list[TranscriptUtterance]


@dataclass(frozen=True)
class SpeakerTurn:
    start_ms: int
    end_ms: int
    speaker: str


@dataclass(frozen=True)
class AnalysisSection:
    sequence: int
    title: str
    start_ms: int
    end_ms: int
    summary: str
    keywords: list[str]


@dataclass(frozen=True)
class AnalysisResult:
    one_line_summary: str
    detailed_summary: str
    keywords: list[str]
    sections: list[AnalysisSection]


class SpeechToTextProvider(Protocol):
    def transcribe(self, audio_path: str) -> TranscriptResult: ...


class SpeakerDiarizationProvider(Protocol):
    def diarize(self, audio_path: str) -> list[SpeakerTurn]: ...


class CallAnalysisProvider(Protocol):
    def analyze(self, transcript: TranscriptResult) -> AnalysisResult: ...
