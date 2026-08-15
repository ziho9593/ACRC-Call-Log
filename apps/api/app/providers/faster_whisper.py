from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .base import SpeechToTextProvider, TranscriptResult, TranscriptUtterance

ModelFactory = Callable[..., Any]


class FasterWhisperSpeechToTextProvider(SpeechToTextProvider):
    def __init__(
        self,
        model_path: Path,
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "ko",
        model_factory: ModelFactory | None = None,
    ) -> None:
        if not model_path.is_dir():
            raise FileNotFoundError(f"Whisper 모델 디렉터리를 찾을 수 없습니다: {model_path}")

        if model_factory is None:
            from faster_whisper import WhisperModel

            model_factory = WhisperModel

        self._language = language
        self._model = model_factory(
            str(model_path),
            device=device,
            compute_type=compute_type,
            local_files_only=True,
        )

    def transcribe(self, audio_path: str) -> TranscriptResult:
        segments, info = self._model.transcribe(
            audio_path,
            language=self._language,
            beam_size=5,
            vad_filter=True,
        )

        utterances: list[TranscriptUtterance] = []
        last_end_ms = 0
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue

            start_ms = round(segment.start * 1000)
            end_ms = round(segment.end * 1000)
            last_end_ms = max(last_end_ms, end_ms)
            utterances.append(
                TranscriptUtterance(
                    sequence=len(utterances) + 1,
                    speaker="화자",
                    start_ms=start_ms,
                    end_ms=end_ms,
                    text=text,
                )
            )

        detected_duration_ms = round(float(getattr(info, "duration", 0)) * 1000)
        return TranscriptResult(
            duration_ms=max(detected_duration_ms, last_end_ms),
            utterances=utterances,
        )
